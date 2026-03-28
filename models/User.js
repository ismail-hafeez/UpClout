const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const userSchema = new mongoose.Schema({
  username: {
    type: String,
    required: true,
    unique: true,
    trim: true,
    minlength: 3,
    maxlength: 30,
  },
  email: {
    type: String,
    required: true,
    unique: true,
    trim: true,
    lowercase: true,
  },
  password: {
    type: String,
    required: true,
    minlength: 6,
  },
  displayName: {
    type: String,
    trim: true,
    default: '',
  },
  avatarUrl: {
    type: String,
    default: '',
  },
  // Ready for Instagram later — just populate these fields
  instagramId: { type: String, default: null },
  instagramHandle: { type: String, default: null },
  instagramAccessToken: { type: String, default: null },
  cloutScore: { type: Number, default: 0 },
  reviewCount: { type: Number, default: 0 },
  userType: { type: String, enum: ['Influencer', 'Brand'], default: 'Influencer' },
}, { timestamps: true });

// Hash password before saving
userSchema.pre('save', async function (next) {
  if (!this.isModified('password')) return next();
  this.password = await bcrypt.hash(this.password, 12);
  next();
});

// Compare password helper
userSchema.methods.comparePassword = async function (candidate) {
  return bcrypt.compare(candidate, this.password);
};

// Never send password in responses
userSchema.methods.toSafeObject = function () {
  return {
    id: this._id,
    username: this.username,
    email: this.email,
    displayName: this.displayName || this.username,
    avatarUrl: this.avatarUrl,
    cloutScore: this.cloutScore,
    reviewCount: this.reviewCount,
    userType: this.userType,
  };
};

module.exports = mongoose.model('User', userSchema);