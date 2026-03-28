const express = require('express');
const router = express.Router();
const User = require('../models/User');
const Review = require('../models/Review');
const Connection = require('../models/Connection');
const { protect } = require('../middleware/auth');

// ========================
// CONNECTIONS
// ========================

// GET /api/users/connections/requests - Get pending incoming requests
router.get('/connections/requests', protect, async (req, res) => {
  try {
    const requests = await Connection.find({ recipient: req.user._id, status: 'pending' })
      .populate('requester', 'username displayName avatarUrl cloutScore');
    res.json(requests);
  } catch (err) {
    res.status(500).json({ message: 'Error fetching requests' });
  }
});

// GET /api/users/connections/accepted - Get all accepted connections
router.get('/connections/accepted', protect, async (req, res) => {
  try {
    const connections = await Connection.find({
      $or: [{ requester: req.user._id }, { recipient: req.user._id }],
      status: 'accepted'
    }).populate('requester', 'username displayName avatarUrl cloutScore')
      .populate('recipient', 'username displayName avatarUrl cloutScore');
    
    // Map to return the *other* user in each connection
    const friends = connections.map(conn => {
      return conn.requester._id.toString() === req.user._id.toString() ? conn.recipient : conn.requester;
    });
    
    res.json(friends);
  } catch (err) {
    res.status(500).json({ message: 'Error fetching accepted connections' });
  }
});

// POST /api/users/connections/:reqId/accept
router.post('/connections/:reqId/accept', protect, async (req, res) => {
  try {
    const conn = await Connection.findById(req.params.reqId);
    if (!conn) return res.status(404).json({ message: 'Request not found' });
    if (conn.recipient.toString() !== req.user._id.toString()) return res.status(403).json({ message: 'Unauthorized' });
    
    conn.status = 'accepted';
    await conn.save();
    res.json(conn);
  } catch (err) {
    res.status(500).json({ message: 'Error accepting request' });
  }
});

// POST /api/users/connections/:reqId/reject
router.post('/connections/:reqId/reject', protect, async (req, res) => {
  try {
    const conn = await Connection.findById(req.params.reqId);
    if (!conn) return res.status(404).json({ message: 'Request not found' });
    if (conn.recipient.toString() !== req.user._id.toString()) return res.status(403).json({ message: 'Unauthorized' });
    
    await Connection.findByIdAndDelete(req.params.reqId);
    res.json({ message: 'Rejected' });
  } catch (err) {
    res.status(500).json({ message: 'Error rejecting request' });
  }
});

// DELETE /api/users/connections/:reqId - Unadd / delete connection
router.delete('/connections/:reqId', protect, async (req, res) => {
  try {
    const conn = await Connection.findById(req.params.reqId);
    if (!conn) return res.status(404).json({ message: 'Connection not found' });
    if (conn.recipient.toString() !== req.user._id.toString() && conn.requester.toString() !== req.user._id.toString()) {
       return res.status(403).json({ message: 'Unauthorized' });
    }
    
    await Connection.findByIdAndDelete(req.params.reqId);
    res.json({ message: 'Connection removed' });
  } catch (err) {
    res.status(500).json({ message: 'Error removing connection' });
  }
});

// GET /api/users/:id/connection-status - Get relationship status
router.get('/:id/connection-status', protect, async (req, res) => {
  try {
    if (req.params.id === req.user._id.toString()) return res.json({ status: 'self' });
    const conn = await Connection.findOne({
      $or: [
        { requester: req.user._id, recipient: req.params.id },
        { requester: req.params.id, recipient: req.user._id }
      ]
    });
    if (!conn) return res.json({ status: 'none' });
    
    res.json({ 
      status: conn.status, 
      isRequester: conn.requester.toString() === req.user._id.toString(),
      connectionId: conn._id 
    });
  } catch (err) {
    res.status(500).json({ message: 'Error checking status' });
  }
});

// POST /api/users/:id/connect - Send request
router.post('/:id/connect', protect, async (req, res) => {
  try {
    if (req.params.id === req.user._id.toString()) return res.status(400).json({ message: 'Cannot connect to self' });
    
    const existing = await Connection.findOne({
      $or: [
        { requester: req.user._id, recipient: req.params.id },
        { requester: req.params.id, recipient: req.user._id }
      ]
    });

    if (existing) {
      if (existing.status === 'pending' && existing.recipient.toString() === req.user._id.toString()) {
        existing.status = 'accepted';
        await existing.save();
        return res.json({ status: 'accepted' });
      }
      return res.json({ status: existing.status });
    }

    const conn = await Connection.create({ requester: req.user._id, recipient: req.params.id, status: 'pending' });
    res.json({ status: 'pending', connectionId: conn._id });
  } catch (err) {
    res.status(500).json({ message: 'Error connecting' });
  }
});

// ========================
// USERS & REVIEWS
// ========================

// GET /api/users/:id - Get public user profile
router.get('/:id', async (req, res) => {
  try {
    const user = await User.findById(req.params.id)
      .select('_id username displayName avatarUrl cloutScore reviewCount createdAt');
    if (!user) return res.status(404).json({ message: 'User not found' });
    res.json(user);
  } catch (err) {
    res.status(500).json({ message: 'Server error fetching user profile' });
  }
});

// GET /api/users/:id/reviews - Get reviews for a user
router.get('/:id/reviews', async (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 20;
    const page = parseInt(req.query.page) || 1;
    const skip = (page - 1) * limit;

    const reviews = await Review.find({ targetUser: req.params.id })
      .sort({ createdAt: -1 })
      .skip(skip)
      .limit(limit)
      .populate('reviewer', 'username displayName avatarUrl');

    const total = await Review.countDocuments({ targetUser: req.params.id });

    res.json({ reviews, total, page, totalPages: Math.ceil(total / limit) });
  } catch (err) {
    res.status(500).json({ message: 'Server error fetching reviews' });
  }
});

// POST /api/users/:id/reviews - Submit or update a review
router.post('/:id/reviews', protect, async (req, res) => {
  try {
    const targetUserId = req.params.id;
    const { rating, comment } = req.body;

    if (targetUserId === req.user._id.toString()) {
      return res.status(400).json({ message: 'You cannot review yourself.' });
    }

    if (!rating || rating < 1 || rating > 5) {
      return res.status(400).json({ message: 'Rating must be between 1 and 5.' });
    }

    // Verify connection to leave review
    const conn = await Connection.findOne({
      $or: [
        { requester: req.user._id, recipient: targetUserId },
        { requester: targetUserId, recipient: req.user._id }
      ],
      status: 'accepted'
    });
    if (!conn) {
      return res.status(403).json({ message: 'You must be connected to leave a review.' });
    }

    // Upsert review (allows a user to update their existing review)
    await Review.findOneAndUpdate(
      { reviewer: req.user._id, targetUser: targetUserId },
      { rating, comment },
      { upsert: true, new: true, setDefaultsOnInsert: true }
    );

    // Recalculate average rating
    const mongoose = require('mongoose');
    const stats = await Review.aggregate([
      { $match: { targetUser: new mongoose.Types.ObjectId(targetUserId) } },
      { $group: {
          _id: '$targetUser',
          averageRating: { $avg: '$rating' },
          numOfReviews: { $sum: 1 }
      }}
    ]);

    const cloutScore = stats.length > 0 ? Number(stats[0].averageRating.toFixed(1)) : 0;
    const reviewCount = stats.length > 0 ? stats[0].numOfReviews : 0;

    await User.findByIdAndUpdate(targetUserId, { $set: { cloutScore, reviewCount } });

    res.json({ message: 'Review submitted successfully', cloutScore, reviewCount });
  } catch (err) {
    console.error('Submit review error:', err);
    res.status(500).json({ message: 'Failed to submit review' });
  }
});

module.exports = router;
