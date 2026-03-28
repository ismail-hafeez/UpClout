const express = require('express');
const router = express.Router();
const Campaign = require('../models/Campaign');
const { protect } = require('../middleware/auth');

// POST /api/campaigns - Create a new campaign
router.post('/', protect, async (req, res) => {
  try {
    const { title, goal, budget, niche, timeline } = req.body;
    const campaign = await Campaign.create({
      title,
      goal,
      budget,
      niche,
      timeline,
      brandId: req.user._id,
      status: 'Active',
      startDate: new Date()
    });
    res.status(201).json(campaign);
  } catch (err) {
    console.error('Create campaign error:', err);
    res.status(500).json({ message: 'Error creating campaign' });
  }
});

// GET /api/campaigns - Get user's campaigns
router.get('/', protect, async (req, res) => {
  try {
    const campaigns = await Campaign.find({ brandId: req.user._id }).sort({ createdAt: -1 });
    res.json(campaigns);
  } catch (err) {
    console.error('Fetch campaigns error:', err);
    res.status(500).json({ message: 'Error fetching campaigns' });
  }
});

router.put('/:id/status', protect, async (req, res) => {
  try {
    const campaign = await Campaign.findOne({ _id: req.params.id, brandId: req.user._id });
    if (!campaign) return res.status(404).json({ message: 'Campaign not found' });

    campaign.status = req.body.status;
    
    if (req.body.status === 'Completed') {
      campaign.completionDate = new Date();
      const Collaboration = require('../models/Collaboration');
      await Collaboration.updateMany({ campaignId: campaign._id }, { status: 'Completed' });
    }
    
    await campaign.save();

    res.json(campaign);
  } catch (err) {
    console.error('Update campaign status error:', err);
    res.status(500).json({ message: 'Error updating status' });
  }
});

module.exports = router;
