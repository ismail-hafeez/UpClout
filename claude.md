### Implement this plan

## Owly Chat

1. The chat should support past conversation histories as well. Use mongoDb to store conversations
2. The past conversations should have context of the conversation when the user is chatting with. So if i go back to the chat, the previous conversation should be there with context. It should remember what i was asking about.
3. The owly chat should KNOW the user. It should know if the user is an influencer or brand. It should know the user's interests, niche, location, etc. I should NOT have to tell owly anything about myself. It should already know.
4. Ground Owly - it should NEVER suggest brands/influencers that are NOT in the database.
5. Retreival should be improved. Don't just look at the current message. Look at the whole conversation and find relevant information from the past conversations as well.
6. If owly retreives followers/following counts, it should use the correct values and should NOT make up values.
7. These implementations should be done in the owly that is connect to frontend (located in backend-fastapi folder) 
