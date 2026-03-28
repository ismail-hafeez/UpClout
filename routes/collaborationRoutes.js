const express = require('express');
const router = express.Router();
const Collaboration = require('../models/Collaboration');
const { protect } = require('../middleware/auth');

router.post('/', protect, async (req, res) => {
  try {
    const { campaignId, influencerId, deliverables, paymentAmount, currency } = req.body;
    const existing = await Collaboration.findOne({ campaignId, influencerId });
    if (existing) {
      return res.status(400).json({ message: 'Collaboration already exists for this influencer and campaign.' });
    }
    const collab = await Collaboration.create({
      campaignId, influencerId, brandId: req.user._id,
      deliverables: deliverables || [],
      paymentDetails: { amount: paymentAmount, currency: currency || 'USD', status: 'Pending' },
      status: 'Negotiating',
      isNew: true
    });
    res.status(201).json(collab);
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: 'Error creating collaboration' });
  }
});

router.put('/mark-seen', protect, async (req, res) => {
  try {
    // Aggressively match anything that isn't explicitly isNew: false
    await Collaboration.updateMany({ influencerId: req.user._id, isNew: { $ne: false } }, { isNew: false });
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ message: 'Error marking collaborations as seen' });
  }
});

router.get('/', protect, async (req, res) => {
  try {
    const collabs = await Collaboration.find({
      $or: [{ brandId: req.user._id }, { influencerId: req.user._id }]
    }).populate('campaignId').populate('brandId', 'username displayName avatarUrl').populate('influencerId', 'username displayName avatarUrl').sort({ createdAt: -1 });
    res.json(collabs);
  } catch (err) {
    res.status(500).json({ message: 'Error fetching collaborations' });
  }
});

router.get('/user/:userId', protect, async (req, res) => {
  try {
    // Only allow the user themselves to see their own collaborations list on their profile
    if (req.user._id.toString() !== req.params.userId) {
      return res.json([]); // Return empty list instead of 403 to maintain privacy without errors
    }
    const collabs = await Collaboration.find({
      $or: [{ brandId: req.params.userId }, { influencerId: req.params.userId }]
    }).populate('campaignId', 'title').populate('brandId', 'username displayName avatarUrl').populate('influencerId', 'username displayName avatarUrl').sort({ createdAt: -1 });
    res.json(collabs);
  } catch (err) {
    res.status(500).json({ message: 'Error fetching public collaborations' });
  }
});

router.put('/:id/status', protect, async (req, res) => {
  try {
    const collab = await Collaboration.findById(req.params.id);
    if (!collab) return res.status(404).json({ message: 'Not found' });
    collab.status = req.body.status;
    await collab.save();
    res.json(collab);
  } catch (err) { res.status(500).json({ message: 'Error' }); }
});

router.put('/:id/deliverables', protect, async (req, res) => {
  try {
    const collab = await Collaboration.findById(req.params.id);
    if (!collab) return res.status(404).json({ message: 'Not found' });
    collab.deliverables = req.body.deliverables;
    await collab.save();
    res.json(collab);
  } catch (err) { res.status(500).json({ message: 'Error' }); }
});

router.put('/:id/payment', protect, async (req, res) => {
  try {
    const collab = await Collaboration.findById(req.params.id);
    if (!collab) return res.status(404).json({ message: 'Not found' });
    collab.paymentDetails.status = req.body.status;
    await collab.save();
    res.json(collab);
  } catch (err) { res.status(500).json({ message: 'Error' }); }
});

module.exports = router;
