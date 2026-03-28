const mongoose = require('mongoose');

const campaignSchema = new mongoose.Schema({
  title: { type: String, required: true },
  goal: { type: String, required: true },
  budget: { type: Number, required: true },
  niche: { type: String, default: '' },
  timeline: { type: String, default: '' },
  brandId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  startDate: { type: Date },
  completionDate: { type: Date },
  status: { type: String, enum: ['Active', 'Paused', 'Completed', 'Draft'], default: 'Active' },
}, { timestamps: true });

module.exports = mongoose.model('Campaign', campaignSchema);
