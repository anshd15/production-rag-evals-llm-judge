# Judge vs human agreement (60 drafts, run `final_vertex`)

| Criterion | Human pass | Judge pass | Agreement | Cohen's κ |
|---|---|---|---|---|
| addresses_issue | 92% | 70% | 78% | 0.35 |
| grounded | 73% | 92% | 75% | 0.18 |
| correct_next_step | 68% | 62% | 87% | 0.71 |
| tone | 97% | 98% | 95% | -0.02 |
| safe | 100% | 100% | 100% | n/a |
| would_send | 62% | 53% | 82% | 0.63 |

**would_send confusion (rows = human, cols = judge):**

| | judge yes | judge no |
|---|---|---|
| human yes | 29 | 8 |
| human no | 3 | 20 |

**would_send by system (human vs judge):** agent: 87% vs 73% (n=30), simple: 55% vs 45% (n=20), trivial: 0% vs 10% (n=10)

## Disagreements on would_send

- **Tweet:** Yeah it's not working
  - Draft: That's frustrating. Could you DM us your account's email address? We'll take a closer look at what's going on [link]
  - Human: send · Judge: edit — The draft asks for account details for a known service-wide issue that was already being addressed, making the request for personal information unnecessary and potentially confusing.
- **Tweet:** im serious problems because nothing about my premium acount. Help me __email__
  - Draft: We've already replied to your DM. We'll carry on helping out there
  - Human: send · Judge: edit — The draft makes an unsubstantiated claim that a DM conversation has already occurred and fails to address the customer's immediate need for help or the security risk of their public email.
- **Tweet:** I want to know if you guys charge for the month past or coming month ??? Please answer me!!
  - Draft: Hi! We've replied to your DM. We'll continue helping there
  - Human: send · Judge: edit — The draft claims a DM has already been sent when it has not, which is a false statement regarding the current state of the interaction.
- **Tweet:** When @user uploads your new song to the wrong account AGAIN 🙃☹️ @user and @user plzplzplz stop this from happening to ussssss we love uuuuu plz love us backkkkk
  - Draft: Hey there! Help's here. Can you send us the artist link? Just tap the three dots > Share > Copy Link. We'll check what's happening backstage 🎧
  - Human: send · Judge: edit — While the tone is good, the draft suggests Spotify support can fix the distribution error directly, whereas the reference correctly identifies that the distributor must be contacted to resolve mapping
- **Tweet:** what’s the update on the Taylor Swift album
  - Draft: Hey! Fingers crossed we'll be able to have it soon, but there's info about Spotify content here: [link]
  - Human: edit · Judge: send — The draft is helpful, on-brand, and provides a relevant resource for content availability without making false promises.
- **Tweet:** Dear @user! As a fresh father and bi #Spotify fan, may I ask you to add some #real #chillout #music for my #newborn #baby like the following: [link] #ThankYou #
  - Draft: Hey there, thanks for the request! We’ll have it available to you as soon as it’s available to us. More info about Spotify content here: [link]
  - Human: edit · Judge: send — The draft is concise, helpful, and provides the correct link for content requests while maintaining a professional and friendly tone.
- **Tweet:** Upgraded to @user premium via family plan. Clicked to invite family members and entered info. Realized after it was asking me to confirm MY details with no way 
  - Draft: Thanks for sharing this feedback with us! We'll make sure to pass your thoughts on the Family plan setup process along to the right team. Let us know if you need help with anything else!
  - Human: send · Judge: edit — While the draft acknowledges the feedback, it fails to offer the necessary support to investigate the user's specific account issue, which requires a DM to resolve.
- **Tweet:** This is the most annoying thing of all time @user [link]
  - Draft: We hear you! We'll pass your feedback on to the right folks so they can check it out. Let us know if you need help with anything else.
  - Human: send · Judge: edit — The draft fails to address the specific technical limitation mentioned in the link provided by the customer, opting for a generic response instead.
- **Tweet:** Yeah - it came back online just as I was leaving the gym! #quietsession
  - Draft: Glad to hear it's working now! For anything else, just give us a shout. [link] 🙂
  - Human: send · Judge: edit — The draft includes an unnecessary link which was not part of the reference or the context of the conversation.
- **Tweet:** Is there a way to reset my listening history? I let my son have access to my account while I was traveling out of range of Spotify. Now everything is populated 
  - Draft: Hey! Can you DM us your account's email address? We'll see what we can suggest [link]
  - Human: send · Judge: edit — The draft fails to address the customer's specific question about resetting their listening history, making it feel like generic boilerplate.
- **Tweet:** trying to hide their incompetencies. Users are paying premium for your service and you try to hide the problems we experience. [link]
  - Draft: Hey there! Sorry for the trouble. Can you let us know your device, OS, and Spotify version? We'll take a closer look.
  - Human: edit · Judge: send — The draft is a valid troubleshooting approach that is professional and helpful, even if it differs slightly from the reference reply's specific request for account details.
