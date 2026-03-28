const mongoose = require('mongoose');

const deliverableSchema = new mongoose.Schema({
  type: { type: String, required: true }, 
  status: { type: String, enum: ['Pending', 'Submitted', 'Approved', 'Rejected'], default: 'Pending' },
  link: { type: String, default: '' }
});

const collaborationSchema = new mongoose.Schema({
  campaignId: { type: mongoose.Schema.Types.ObjectId, ref: 'Campaign', required: true },
  influencerId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  brandId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  deliverables: [deliverableSchema],
  paymentDetails: {
    amount: { type: Number, required: true },
    currency: { type: String, default: 'USD' },
    status: { type: String, enum: ['Pending', 'Paid'], default: 'Pending' }
  },
  status: { type: String, enum: ['Negotiating', 'Content Creation', 'Content Review', 'Completed'], default: 'Negotiating' },
  isNew: { type: Boolean, default: false }
}, { timestamps: true });

module.exports = mongoose.model('Collaboration', collaborationSchema);
