//  TYPES 
export interface Message {
  id: string;
  text: string;
  sender: "me" | "other" | "owly";
  timestamp: string;
  avatar?: string;
}

export interface Chat {
  id: string;
  name: string;
  avatar: string;
  lastMessage: string;
  time: string;
  unread: number;
}

// MOCK INFLUENCER AVATARS 
export const AVATARS = {
  influencer1: `data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='50' fill='%23e05a2b'/><circle cx='50' cy='38' r='18' fill='%23f4a87c'/><ellipse cx='50' cy='80' rx='26' ry='20' fill='%23f4a87c'/><circle cx='50' cy='38' r='18' fill='%23f4a87c'/><path d='M32 35 Q50 18 68 35' fill='%23c0392b'/></svg>`,
  influencer2: `data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='50' fill='%232ecc71'/><circle cx='50' cy='38' r='18' fill='%23a8e6b8'/><ellipse cx='50' cy='80' rx='26' ry='20' fill='%23a8e6b8'/></svg>`,
  influencer3: `data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='50' fill='%239b59b6'/><circle cx='50' cy='38' r='18' fill='%23d7bde2'/><ellipse cx='50' cy='80' rx='26' ry='20' fill='%23d7bde2'/></svg>`,
  me: `data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='50' fill='%232563eb'/><circle cx='50' cy='38' r='18' fill='%23bfdbfe'/><ellipse cx='50' cy='80' rx='26' ry='20' fill='%23bfdbfe'/><rect x='30' y='18' width='40' height='14' rx='4' fill='%23f59e0b'/></svg>`,
};

//  MOCK CHATS 
export const mockChats: Chat[] = [
  {
    id: "1",
    name: "Hania Amir",
    avatar: AVATARS.influencer1,
    lastMessage: "Sounds great! I can do the post next Tuesday.",
    time: "2m ago",
    unread: 1,
  },
  {
    id: "2",
    name: "Ducky Bhai",
    avatar: AVATARS.influencer2,
    lastMessage: "What's the deliverable for the campaign?",
    time: "1h ago",
    unread: 0,
  },
  {
    id: "3",
    name: "Mahira Khan",
    avatar: AVATARS.influencer3,
    lastMessage: "Let me check my schedule and get back to you.",
    time: "3h ago",
    unread: 0,
  },
];

// MOCK MESSAGES FOR USER CHAT 
export const mockMessages: Message[] = [
  {
    id: "1",
    sender: "other",
    text: "Hey! I saw your brand brief — looks super interesting. I'd love to collaborate on this campaign.",
    timestamp: "10:22 AM",
    avatar: AVATARS.influencer1,
  },
  {
    id: "2",
    sender: "me",
    text: "That's great to hear! We're looking for someone with your aesthetic. The campaign runs through March and we have a budget of $2,500 for 3 posts + stories.",
    timestamp: "10:24 AM",
    avatar: AVATARS.me,
  },
  {
    id: "3",
    sender: "other",
    text: "That works for me. Can you share the product samples? I like to feature things I've actually used.",
    timestamp: "10:27 AM",
    avatar: AVATARS.influencer1,
  },
  {
    id: "4",
    sender: "me",
    text: "Absolutely, we'll ship samples this week!",
    timestamp: "10:28 AM",
    avatar: AVATARS.me,
  },
];

// MOCK OWLY MESSAGES 
export const mockOwlyMessages: Message[] = [
  {
    id: "1",
    sender: "owly",
    text: "Hi! I'm Owly, your AI assistant. Tell me about your campaign and I'll find the perfect influencers for you!",
    timestamp: "10:00 AM",
  },
  {
    id: "2",
    sender: "me",
    text: "I need fitness influencers in the US with 50k-200k followers who focus on sustainable living.",
    timestamp: "10:01 AM",
    avatar: AVATARS.me,
  },
  {
    id: "3",
    sender: "owly",
    text: "Great brief! I found 24 matching influencers. Top picks include @greenfit.life (142k followers, 4.8% engagement), @sustainablesweats (89k, 5.2%), and @earthmovements (67k, 6.1%). Want me to reach out to any of them on your behalf?",
    timestamp: "10:01 AM",
  },
];