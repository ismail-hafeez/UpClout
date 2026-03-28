const express = require('express');
const mongoose = require('mongoose');
const Conversation = require('../models/Conversation');
const Message = require('../models/Message');
const User = require('../models/User');
const Connection = require('../models/Connection');
const { protect } = require('../middleware/auth');
const multer = require('multer');
const path = require('path');
const fs = require('fs');

const router = express.Router();

// File upload setup — saves to backend/uploads/
const uploadDir = path.join(__dirname, '..', 'uploads');
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir);

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadDir),
  filename: (req, file, cb) => {
    const unique = `${Date.now()}-${Math.round(Math.random() * 1e9)}`;
    cb(null, unique + path.extname(file.originalname));
  },
});

const upload = multer({
  storage,
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB
});

// GET /api/conversations — all conversations for current user
router.get('/', protect, async (req, res) => {
  try {
    const conversations = await Conversation.find({
      participants: req.user._id,
    })
      .populate('participants', 'username displayName avatarUrl')
      .populate('lastMessage')
      .sort({ lastMessageAt: -1 });

    // Shape each conversation for the frontend
    const shaped = conversations.map((conv) => {
      const other = conv.participants.find(
        (p) => p._id.toString() !== req.user._id.toString()
      );
      return {
        id: conv._id,
        otherUser: other,
        lastMessage: conv.lastMessage?.text || '',
        lastMessageAt: conv.lastMessageAt,
        unread: conv.unreadCounts?.get(req.user._id.toString()) || 0,
      };
    });

    res.json(shaped);
  } catch (err) {
    console.error('Get conversations error:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

// POST /api/conversations — start or get existing conversation with a user
router.post('/', protect, async (req, res) => {
  try {
    const { recipientId } = req.body;
    if (!recipientId) {
      return res.status(400).json({ message: 'recipientId is required' });
    }

    const recipient = await User.findById(recipientId);
    if (!recipient) {
      return res.status(404).json({ message: 'User not found' });
    }

    const conn = await Connection.findOne({
      $or: [
        { requester: req.user._id, recipient: recipientId },
        { requester: recipientId, recipient: req.user._id }
      ],
      status: 'accepted'
    });
    if (!conn) {
      return res.status(403).json({ message: 'You must be connected to start a conversation' });
    }

    // Check if conversation already exists
    let conversation = await Conversation.findOne({
      participants: { $all: [req.user._id, recipientId], $size: 2 },
    });

    if (!conversation) {
      conversation = await Conversation.create({
        participants: [req.user._id, recipientId],
      });
    }

    await conversation.populate('participants', 'username displayName avatarUrl');

    res.json(conversation);
  } catch (err) {
    console.error('Create conversation error:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

// GET /api/conversations/:id/messages — fetch messages (paginated)
router.get('/:id/messages', protect, async (req, res) => {
  try {
    const { page = 1, limit = 40 } = req.query;
    const skip = (page - 1) * limit;

    const messages = await Message.find({ conversationId: req.params.id })
      .populate('sender', 'username displayName avatarUrl')
      .sort({ createdAt: 1 })
      .skip(skip)
      .limit(Number(limit));

    // Mark messages as read
    await Message.updateMany(
      {
        conversationId: req.params.id,
        readBy: { $ne: req.user._id },
        sender: { $ne: req.user._id },
      },
      { $addToSet: { readBy: req.user._id } }
    );

    // Reset unread count for this user
    await Conversation.findByIdAndUpdate(req.params.id, {
      $set: { [`unreadCounts.${req.user._id}`]: 0 },
    });

    res.json(messages);
  } catch (err) {
    console.error('Get messages error:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

// POST /api/conversations/:id/files — upload a file in a conversation
router.post('/:id/files', protect, upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ message: 'No file uploaded' });
    }

    const conversation = await Conversation.findById(req.params.id);
    if (!conversation) return res.status(404).json({ message: 'Conversation not found' });

    const otherParticipantId = conversation.participants.find(p => p.toString() !== req.user._id.toString());
    if (otherParticipantId) {
       const conn = await Connection.findOne({
         $or: [
           { requester: req.user._id, recipient: otherParticipantId },
           { requester: otherParticipantId, recipient: req.user._id }
         ],
         status: 'accepted'
       });
       if (!conn) return res.status(403).json({ message: 'You must be connected to send files' });
    }

    const message = await Message.create({
      conversationId: req.params.id,
      sender: req.user._id,
      text: '',
      file: {
        originalName: req.file.originalname,
        mimeType: req.file.mimetype,
        size: req.file.size,
        url: `/uploads/${req.file.filename}`,
      },
      readBy: [req.user._id],
    });

    // Update conversation lastMessage
    await Conversation.findByIdAndUpdate(req.params.id, {
      lastMessage: message._id,
      lastMessageAt: new Date(),
    });

    await message.populate('sender', 'username displayName avatarUrl');
    res.status(201).json(message);
  } catch (err) {
    console.error('File upload error:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

// GET /api/users/search?q=username — find users to start a chat
router.get('/users/search', protect, async (req, res) => {
  try {
    const { q } = req.query;
    if (!q || q.length < 2) {
      return res.json([]);
    }

    const users = await User.find({
      _id: { $ne: req.user._id },
      $or: [
        { username: { $regex: q, $options: 'i' } },
        { displayName: { $regex: q, $options: 'i' } },
      ],
    })
      .select('username displayName avatarUrl')
      .limit(10);

    res.json(users);
  } catch (err) {
    console.error('User search error:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;