const jwt = require('jsonwebtoken');
const Message = require('../models/Message');
const Conversation = require('../models/Conversation');
const User = require('../models/User');
const Connection = require('../models/Connection');

// Map of userId -> socketId for online presence
const onlineUsers = new Map();

const initSocket = (io) => {
  // Authenticate socket connection via JWT
  io.use(async (socket, next) => {
    try {
      const token = socket.handshake.auth.token;
      if (!token) return next(new Error('Authentication required'));

      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      const user = await User.findById(decoded.id).select('-password');
      if (!user) return next(new Error('User not found'));

      socket.user = user;
      next();
    } catch (err) {
      next(new Error('Invalid token'));
    }
  });

  io.on('connection', (socket) => {
    const userId = socket.user._id.toString();
    onlineUsers.set(userId, socket.id);

    // Tell everyone this user is online
    socket.broadcast.emit('user:online', { userId });

    // Join a room per conversation
    socket.on('conversation:join', (conversationId) => {
      socket.join(conversationId);
    });

    socket.on('conversation:leave', (conversationId) => {
      socket.leave(conversationId);
    });

    // Handle sending a text message
    socket.on('message:send', async (data, callback) => {
      try {
        const { conversationId, text } = data;

        if (!text?.trim()) {
          return callback?.({ error: 'Message cannot be empty' });
        }

        // Verify sender is a participant
        const conversation = await Conversation.findOne({
          _id: conversationId,
          participants: socket.user._id,
        });
        if (!conversation) {
          return callback?.({ error: 'Conversation not found' });
        }

        const otherParticipantId = conversation.participants.find(p => p.toString() !== socket.user._id.toString());
        if (otherParticipantId) {
          const conn = await Connection.findOne({
            $or: [
               { requester: socket.user._id, recipient: otherParticipantId },
               { requester: otherParticipantId, recipient: socket.user._id }
            ],
            status: 'accepted'
          });
          if (!conn) return callback?.({ error: 'not_connected' });
        }

        // Save message to DB
        const message = await Message.create({
          conversationId,
          sender: socket.user._id,
          text: text.trim(),
          readBy: [socket.user._id],
        });

        await message.populate('sender', 'username displayName avatarUrl');

        // Update conversation metadata
        const otherParticipants = conversation.participants
          .map((p) => p.toString())
          .filter((p) => p !== userId);

        const unreadUpdate = {};
        for (const participantId of otherParticipants) {
          const current = conversation.unreadCounts?.get(participantId) || 0;
          unreadUpdate[`unreadCounts.${participantId}`] = current + 1;
        }

        await Conversation.findByIdAndUpdate(conversationId, {
          lastMessage: message._id,
          lastMessageAt: new Date(),
          ...unreadUpdate,
        });

        // Broadcast to all in the conversation room
        io.to(conversationId).emit('message:new', message);

        // Also notify recipients who may not be in the room
        for (const participantId of otherParticipants) {
          const recipientSocketId = onlineUsers.get(participantId);
          if (recipientSocketId) {
            io.to(recipientSocketId).emit('conversation:updated', {
              conversationId,
              lastMessage: message.text,
              lastMessageAt: message.createdAt,
            });
          }
        }

        callback?.({ success: true, message });
      } catch (err) {
        console.error('Socket message:send error:', err);
        callback?.({ error: 'Failed to send message' });
      }
    });

    // Typing indicators
    socket.on('typing:start', ({ conversationId }) => {
      socket.to(conversationId).emit('typing:start', {
        userId,
        username: socket.user.username,
      });
    });

    socket.on('typing:stop', ({ conversationId }) => {
      socket.to(conversationId).emit('typing:stop', { userId });
    });

    socket.on('disconnect', () => {
      onlineUsers.delete(userId);
      socket.broadcast.emit('user:offline', { userId });
    });
  });
};

module.exports = { initSocket };