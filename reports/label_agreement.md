# Human vs LLM labels (200 golden messages)

| | Agreement | Cohen's κ |
|---|---|---|
| intent (11 classes) | 83% | 0.80 |
| escalate (binary) | 91% | 0.79 |

Human escalate rate 33% vs LLM 30%.

## Where they disagree on intent

- human **how_to_usage** vs LLM **technical_issue**: 4
- human **other** vs LLM **technical_issue**: 3
- human **technical_issue** vs LLM **account_access**: 3
- human **how_to_usage** vs LLM **subscription_plan**: 2
- human **subscription_plan** vs LLM **how_to_usage**: 2
- human **subscription_plan** vs LLM **feedback_feature_request**: 2
- human **feedback_feature_request** vs LLM **other**: 2
- human **feedback_feature_request** vs LLM **technical_issue**: 2
- human **artist_creator** vs LLM **other**: 1
- human **account_access** vs LLM **technical_issue**: 1

## Examples (human vs LLM)

- Hey @user, i just signed up for family plan and family members got weird characters for username. How do i change it?
  - human: how_to_usage / auto
  - LLM: technical_issue / escalate
- im serious problems because nothing about my premium acount. Help me __email__
  - human: other / auto
  - LLM: technical_issue / escalate
- you have the wrong 'The Race' on the charts. It isn't a 22 Savage song with 58m plays. Please fix lol. 😂 [link]
  - human: artist_creator / auto
  - LLM: other / auto
- why it keep saying my account in use somewhere else. I have a free acc so how is that
  - human: account_access / escalate
  - LLM: technical_issue / escalate
- Dear @user, you keep asking to go premium again and again. And I just went premium to skip ads, the first thing that happens is I'm unable to get rid of this ad! WTH!! [link]
  - human: technical_issue / escalate
  - LLM: technical_issue / auto
- When @user uploads your new song to the wrong account AGAIN 🙃☹️ @user and @user plzplzplz stop this from happening to ussssss we love uuuuu plz love us backkkkk ❤️ [link]
  - human: artist_creator / escalate
  - LLM: artist_creator / auto
- Can you help us? our EP ‘A Matter Of Opinion’ is being linked to an artist with a similar name we need to be a separate artist and have it as our own. [link]
  - human: artist_creator / escalate
  - LLM: artist_creator / auto
- Hi, is there any update on Spotify for WebOS 3? It's been almost 5 months!
  - human: content_availability / auto
  - LLM: feedback_feature_request / auto
- hey there. I see you're offering premium for 99 cents for 3 months. Can you apply that to my current premium account?
  - human: subscription_plan / escalate
  - LLM: subscription_plan / auto
- i live in canada but I'm paying in my home country in euros. It's both 9.99/month but let's be honest here...9.99 euros aint the same as 9.99 CAD. Can you help me change account se
  - human: how_to_usage / auto
  - LLM: how_to_usage / escalate
- WHY ON EARTH is "Fantastic Baby" by Bigbang written as "Fanstastic Boy"?
  - human: technical_issue / auto
  - LLM: other / auto
- My Facebook won’t connect to my Spotify account. Please help!
  - human: account_access / escalate
  - LLM: account_access / auto
- facebook login not working help pages don't help plz help thanks
  - human: account_access / escalate
  - LLM: account_access / auto
- How to add an account to a new phone as part of family plan?
  - human: how_to_usage / auto
  - LLM: subscription_plan / auto
- Hi, I'd like to subscribe Spotify Premium using Digi billing (Malaysia). But it's not in the payment option. May I know why?
  - human: subscription_plan / auto
  - LLM: how_to_usage / auto
