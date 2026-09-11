# Failure analysis — v1 / dev

## Intent confusions (45 errors / 250)

- gold **technical_issue** → predicted **other**: 7
- gold **other** → predicted **feedback_feature_request**: 4
- gold **billing_payment** → predicted **technical_issue**: 3
- gold **other** → predicted **technical_issue**: 3
- gold **subscription_plan** → predicted **billing_payment**: 3
- gold **technical_issue** → predicted **billing_payment**: 2
- gold **how_to_usage** → predicted **feedback_feature_request**: 2
- gold **subscription_plan** → predicted **how_to_usage**: 2
- gold **praise_thanks** → predicted **technical_issue**: 2
- gold **billing_payment** → predicted **subscription_plan**: 2
- gold **subscription_plan** → predicted **account_access**: 2
- gold **artist_creator** → predicted **content_availability**: 1

### technical_issue → other

- **isn’t working! I have to resort to @user 😱😵**
  - gold: technical_issue / auto · agent: other (0.70) / auto
  - agent reply: Hey! Help's here. Can you tell us what's happening exactly? We'll see what we can suggest
  - brand reply: Hey Marika! We had a little hiccup backstage, but it should be working now. We're here if you need us
- **what is this?? This has happened before but I'm wondering why does spotify keep doing this [link]**
  - gold: technical_issue / auto · agent: other (0.60) / auto
  - agent reply: Hi there! That doesn't look right. Can you let us know what device and Spotify version you're using? We'll see what we can suggest
  - brand reply: Hey, help's here! Just to clarify, are you referring to how your Play Bar looks like? Also, what's the device/OS you're using?
- **. @user why is your app broken af**
  - gold: technical_issue / auto · agent: other (0.60) / auto
  - agent reply: Hey there, help's here! Could you tell us what's happening exactly? We'll see what we can suggest
  - brand reply: Hey, thanks for the report! We had a little hiccup earlier, but everything should be running just fine now

### other → feedback_feature_request

- **..... biggest load of shit app I have ever experienced if your looking for a reason to smash your handset. By all means get SPOTIFY. [link]**
  - gold: other / auto · agent: feedback_feature_request (0.80) / auto
  - agent reply: Hey! Help's here. Could you tell us what's happening exactly? We'll see what we can suggest
  - brand reply: Hey there! That doesn't sound good. Could you DM us exactly what's happening? We'll see what we can suggest [link]
- **" Enjoy 30 minutes of add free music " [link]**
  - gold: other / auto · agent: feedback_feature_request (0.85) / auto
  - agent reply: Hey, that doesn't sound good! Did the app crash at any point during the 30 minutes? That can cause the ad-free time to reset
  - brand reply: Hi Fran! We've just sent a DM your way. Let's carry on chatting there
- **Concerned that your fans first algorithm may have an error as I’m not on your distro list for @user 😳 - lmk if I need to listen to his music 25/7 instead of 24/7 bc I need an invite to his #SpotifyFansFirst concert if he**
  - gold: other / auto · agent: feedback_feature_request (0.70) / auto
  - agent reply: Hey! Thanks for the heads-up. Can you give us more details about what's happening? We'll look into it
  - brand reply: Hey Naomi! We’re afraid the emails are unique and sent to those who listen to Shawn Mendes the most on Spotify. Don't worry, we'll be sure to pass your feedback on to the right folks

### billing_payment → technical_issue

- **Just upgraded to Spotify Premium (because I’m fancy) but it’s still shuffling on my phone? How do I fix this? @user**
  - gold: billing_payment / ESC:account_specific · agent: technical_issue (0.90) / auto
  - agent reply: Hey! Help's here. What device, operating system, and Spotify version are you running? We'll see what we can suggest
  - brand reply: Hi BT! Help's here. Can you DM us your account's username or email address? We'll check things backstage [link]
- **Hi can't update payment info with new payment method. Tried canceling account and that didn't work either. HELP!**
  - gold: billing_payment / ESC:account_specific · agent: technical_issue (0.80) / ESC:troubleshooting_exhausted
  - agent reply: Hey! Can you DM us your account's email address? We'll check what's blocking the update [link]
  - brand reply: Hey Spencer, help's here. Can you DM us your account's email address and username? We'll take a look backstage [link]
- **Once I bought it the app kept skipping through songs and not playing anything but it stops and plays 7 commercials in a row and the skips through every song again.** _(after: Hey, help's here! Can you tell us what's happening exactly? We'll lend a hand)_
  - gold: billing_payment / ESC:billing · agent: technical_issue (0.90) / auto
  - agent reply: Hey! Can you let us know your device's make/model, operating system, and Spotify version? We'll check things out
  - brand reply: That doesn't sound right. Could you DM us your account's email address or username? We'll take a look backstage [link]

### other → technical_issue

- **this has been happening for months and i'm going crazy! i will name my first born son 'spotify cares' if you can help me please and thank you in advance**
  - gold: other / auto · agent: technical_issue (0.85) / auto
  - agent reply: Hey! We'd love to help 😊 Can you tell us exactly what's happening? We'll see what we can suggest
  - brand reply: Hey, we're here to help. Does logging out and back in make a difference? If you could also let us know the exact version of Spotify you're using, that'd be great
- **first off, you are very late. i messaged you over an 30 minuets ago; very disappointing. anyways, my question is how did the picture change? is this some sort of secret witchcraft you have? i need answers & i need them n** _(after: Hey Ky, thanks for reaching out. What’s happening exactly? We'd be happy to help)_
  - gold: other / auto · agent: technical_issue (0.80) / ESC:repeat_contact
  - agent reply: We're sorry for the wait. Can you DM us your account's username and email? We'll look into the profile picture issue [link]
  - brand reply: We understand your frustration. The picture changed because when you open the artist display photo it routes you to their bio photo. If you ever need anything else, just shout and we'll come running 🏃
- **WORK @user**
  - gold: other / auto · agent: technical_issue (0.60) / auto
  - agent reply: Hey! Help's here. Can you tell us what's happening exactly? We'll see what we can suggest
  - brand reply: Hey Liam - we're back in business. Time for you to get back to the music! [link]

## Missed escalations — auto-sent but should escalate (11)

By gold reason: account_specific: 3, repeat_contact: 3, troubleshooting_exhausted: 2, risk: 2, billing: 1
- **Just upgraded to Spotify Premium (because I’m fancy) but it’s still shuffling on my phone? How do I fix this? @user**
  - gold: billing_payment / ESC:account_specific · agent: technical_issue (0.90) / auto
  - agent reply: Hey! Help's here. What device, operating system, and Spotify version are you running? We'll see what we can suggest
  - brand reply: Hi BT! Help's here. Can you DM us your account's username or email address? We'll check things backstage [link]
- **Seems to be affected by my Bluetooth headphones. No issues if I play using my phone's speakers** _(after: That's odd. Can you let us know if this happens over WiFi and/or 4G? We'll be on the looko)_
  - gold: technical_issue / ESC:troubleshooting_exhausted · agent: technical_issue (0.95) / auto
  - agent reply: Got it. For now, we'd recommend using a different headset. Let us know if that helps
  - brand reply: Thanks for letting us know. Do you notice this issue happening with other apps? Also, does restarting your phone help at all?
- **Sure thing.** _(after: We'd suggest deleting your screenshots since they contain private info. Could you DM us in)_
  - gold: other / ESC:risk · agent: other (0.70) / auto
  - agent reply: Thanks for that!
  - brand reply: Great! We'll keep an eye out for your DM
- **It's a Samsung. Thanks. I just get this screen [link]** _(after: Hey Stephanie, help's here! What’s happening exactly? Can you let us know the device/OS yo)_
  - gold: technical_issue / ESC:troubleshooting_exhausted · agent: technical_issue (0.90) / auto
  - agent reply: Thanks! Can you also let us know the exact Android version? Does restarting your device help?
  - brand reply: Hmm. What happens when you tap on any of the icons below? Try logging out > restarting your phone > then logging back in again. Can you also DM us your account's email address? We'll take a look under
- **How can you say you ‘care’ when you obviously have #preset #responses and aren’t interested into looking into the actual complaints #spotifyforgets #transparencynow** _(after: We're sorry you feel that way. It seems we don’t have enough data yet to find the right tr)_
  - gold: dm_status_followup / ESC:repeat_contact · agent: dm_status_followup (0.80) / auto
  - agent reply: We're sorry you feel that way. We do care about each case. Can you tell us specifically what we can help with? [link]
  - brand reply: We understand where you're coming from. Rest assured, we'll pass your feedback onto the right team. Let us know if you have other questions
- **can you help us with this? Our music is getting grouped in with the wrong artist with the same name, and @user has been zero help 🙏🏼🙏🏼🙏🏼🙏🏼🙏🏼🙏🏼 [link]**
  - gold: artist_creator / ESC:repeat_contact · agent: artist_creator (0.90) / auto
  - agent reply: Hey! Thanks for flagging this. Can you send us the Spotify URI? Right-click track > Share > URI. We'll pass it to our team [link]
  - brand reply: Hey - sorry about that! We’d recommend reaching out to your distributor/aggregator. They'll work with our team to make sure your artist page gets fixed up
- **check dm**
  - gold: dm_status_followup / ESC:repeat_contact · agent: dm_status_followup (0.95) / auto
  - agent reply: Hi! We've just sent you a bit more info over DM. We'll carry on helping out there
  - brand reply: Hi Burch! We've just sent you a bit more info over DM. We'll carry on helping out there
- **Sorry! Didn't see this notification. Email should be __email__. connected to my Facebook account of the same name as this one** _(after: Hi there! Can you DM us your account's email address or username? We'll take a look backst)_
  - gold: subscription_plan / ESC:account_specific · agent: account_access (0.80) / auto
  - agent reply: We'd recommend deleting your tweet with your email address for your security. Can you send it via DM instead? [link]
  - brand reply: We don't offer phone support at this time, but you can also contact us via email at [link] We'd suggest deleting your previous tweet as it contains your email address. Can you DM it to us instead, usi

## Needless escalations (28)

By agent reason: account_specific: 19, troubleshooting_exhausted: 2, repeat_contact: 2, billing: 2, security: 2, risk: 1
- **Headphones work fine on all other devices and desktop player of this computer works fine w/o headphones.** _(after: Hmm, that's odd. Is the issue only happening when using your specific computer? Have you t)_
  - gold: technical_issue / auto · agent: technical_issue (0.95) / ESC:troubleshooting_exhausted
  - agent reply: Thanks for testing that. Can you DM us your account's email address or username? We'll take a look backstage [link]
  - brand reply: Do you have any other headphones to try on the computer that you're having issues with? If so, are you getting the same static issue?
  - agent reason: Thorough troubleshooting exhausted; needs account-specific investigation.
- **sort your shit out man don’t have premium for you to not even let me on the app**
  - gold: technical_issue / auto · agent: billing_payment (0.85) / ESC:account_specific
  - agent reply: Hey there! Help's here. Can you DM us your account's email address or username? We'll take a look backstage [link]
  - brand reply: Hey Lewis! Everything should be running smoothly now. Let us know if this is still happening
  - agent reason: Premium subscriber unable to use service; requires account verification and lookup.
- **I can’t login to my account on iOS. It keep showing this message, what should I do? [link]**
  - gold: account_access / auto · agent: account_access (0.90) / ESC:account_specific
  - agent reply: Hey there! We'll help out. Can you DM us your account's email address? We'll take a look under the hood [link]
  - brand reply: Hey! Can you DM us your account's email address? We'll take a look 🔍 [link]
  - agent reason: Account access issue with persistent error; requires account-specific investigation.
- **can’t log into Spotify. I used Facebook credentials to set up my account. Just re downloaded the app on new phone and it won’t log in.**
  - gold: account_access / auto · agent: account_access (0.95) / ESC:account_specific
  - agent reply: Hey, help's here! Can you DM us your account's email address or username? We'll take a look under the hood [link]
  - brand reply: Hi there! Can you DM us your account's email address or username? We'll take a look backstage [link]
  - agent reason: Account access issue with Facebook login; requires account verification.
- **i have a problem with my login...**
  - gold: account_access / auto · agent: account_access (0.95) / ESC:account_specific
  - agent reply: Hey! We'd like to help. Can you DM us your account's email address or username? We'll check backstage [link]
  - brand reply: Hey! We're aware of some potential Spotify for Artists log in issues at the moment. The team are on the case 🙂 If you're struggling, can you DM us your account's email? [link]
  - agent reason: Login issue requires account-specific lookup.
- **. I accidentally subscribed to the Spotify Premium Free Trail while pressing on the mobile phone. Could you help me to unsubscribed to the free trial? I know it's free but I do not want to waste the free trial. My accoun**
  - gold: subscription_plan / auto · agent: subscription_plan (0.90) / ESC:risk
  - agent reply: We can help! First, we'd suggest deleting this tweet to keep your email safe, then DM us with it. We'll help you unsubscribe [link]
  - brand reply: Hey Calvin. We suggest deleting your public post as it contains private info. Can you DM it to us instead? [link]
  - agent reason: Personal data (email) exposed in tweet; customer needs guidance to protect privacy.
- **Another day, another device @user randomly connects to and plays randomly chosen music through. 🙄 How do I stop this from happening without constantly having to unconnect bluetooth? @user**
  - gold: technical_issue / auto · agent: technical_issue (0.90) / ESC:account_specific
  - agent reply: That shouldn't happen! Can you DM us your account's email or username? We'll check what's going on backstage [link]
  - brand reply: Hey, that's not cool! Before anything else, can you DM us your account's email address or username? Knowing what device/version of Spotify you're using would also be helpful. Once we have this info, w
  - agent reason: Recurring device connection issue requires account investigation.
- **first off, you are very late. i messaged you over an 30 minuets ago; very disappointing. anyways, my question is how did the picture change? is this some sort of secret witchcraft you have? i need answers & i need them n** _(after: Hey Ky, thanks for reaching out. What’s happening exactly? We'd be happy to help)_
  - gold: other / auto · agent: technical_issue (0.80) / ESC:repeat_contact
  - agent reply: We're sorry for the wait. Can you DM us your account's username and email? We'll look into the profile picture issue [link]
  - brand reply: We understand your frustration. The picture changed because when you open the artist display photo it routes you to their bio photo. If you ever need anything else, just shout and we'll come running 🏃
  - agent reason: Customer chasing unresponded earlier contact with high frustration.

## Reply failures by rubric criterion (250 judged)

- addresses_issue: 36 fails (14%)
- grounded: 26 fails (10%)
- correct_next_step: 59 fails (24%)
- tone: 2 fails (1%)
- safe: 3 fails (1%)
- would_send: 62 fails (25%)

### Fails `addresses_issue`

- **Headphones work fine on all other devices and desktop player of this computer works fine w/o headphones.** _(after: Hmm, that's odd. Is the issue only happening when using your specific computer? Have you t)_
  - gold: technical_issue / auto · agent: technical_issue (0.95) / ESC:troubleshooting_exhausted
  - agent reply: Thanks for testing that. Can you DM us your account's email address or username? We'll take a look backstage [link]
  - brand reply: Do you have any other headphones to try on the computer that you're having issues with? If so, are you getting the same static issue?
  - judge: Falls back to generic account-DM boilerplate instead of continuing the headphone/hardware diagnostic already underway in the thread.
- **wait whaaaaaaat when did this change come in? o.O** _(after: Hey Bradley! We're afraid we no longer share your listening activity to Facebook. Rest ass)_
  - gold: feedback_feature_request / auto · agent: feedback_feature_request (0.80) / auto
  - agent reply: We're afraid we no longer share your listening activity to Facebook. Rest assured your feedback will be passed on to the right team 🎧
  - brand reply: We can't say exactly when, but we test things out to make the app better. No worries, your feedback matters and this will be passed on. Just give us a shout if you need anything else! 🙂
  - judge: Merely repeats the exact message already sent earlier in the thread instead of responding to the customer's new question about when the change happened.
- **Wtf is this lmao @user @user @user [link]**
  - gold: other / auto · agent: other (0.60) / auto
  - agent reply: Hey! What's happening exactly? Can you tell us more about what you're seeing? We'll help out
  - brand reply: Hey Gracie, help's here! This allows you to view the Stranger Things easter egg feature. Just go to the Now Playing screen and stream this: [link] Let us know if you have any other questions
  - judge: Responds with a generic clarifying question instead of recognizing and explaining the linked content, unlike the reference which directly identified it as the Stranger Things easter egg feature.
- **Sure thing.** _(after: We'd suggest deleting your screenshots since they contain private info. Could you DM us in)_
  - gold: other / ESC:risk · agent: other (0.70) / auto
  - agent reply: Thanks for that!
  - brand reply: Great! We'll keep an eye out for your DM
  - judge: Overly generic acknowledgment that doesn't confirm the team will be watching for the promised DM, unlike the reference.
- **is there any way of me figuring out who appeared on The Indie List playlist last week? i didnt download it and fell in love with so many songs and now cant find them anywhere 😅**
  - gold: how_to_usage / auto · agent: how_to_usage (0.90) / auto
  - agent reply: Hi there! It's currently not possible to view who's on a playlist, but we can see how that'd be useful. Thanks for the feedback 🙂
  - brand reply: Hey Tayla! Unfortunately we're unable to recover last week's The Indie Playlist. Be sure to save your favorites, so you don't miss out in the future. For anything else, just give us a shout ✌️
  - judge: Misreads the request as wanting to view playlist contributors in general, rather than trying to recover last week's specific playlist as the customer actually asked.

### Fails `grounded`

- **On the iphone app the artist page needs to be in alpha order like it is on the ipad. Right now it is a jumbled mess.**
  - gold: feedback_feature_request / auto · agent: feedback_feature_request (0.90) / auto
  - agent reply: Hey! Thanks for the feedback. We can see how that'd be useful. You can vote for the idea here: [link] 🙂
  - brand reply: Hey Rob, help's here! Could you send us a screenshot of what it looks like on your iPhone? We'll take a look
  - judge: Treats an inconsistency the customer says already exists on iPad as an unreleased feature idea, misrepresenting the issue instead of investigating it like the reference did.
- **Seems to be affected by my Bluetooth headphones. No issues if I play using my phone's speakers** _(after: That's odd. Can you let us know if this happens over WiFi and/or 4G? We'll be on the looko)_
  - gold: technical_issue / ESC:troubleshooting_exhausted · agent: technical_issue (0.95) / auto
  - agent reply: Got it. For now, we'd recommend using a different headset. Let us know if that helps
  - brand reply: Thanks for letting us know. Do you notice this issue happening with other apps? Also, does restarting your phone help at all?
  - judge: Jumps to recommending a hardware workaround instead of continuing the diagnostic questioning (e.g., testing across other apps) the reference used to isolate the cause.
- **" Enjoy 30 minutes of add free music " [link]**
  - gold: other / auto · agent: feedback_feature_request (0.85) / auto
  - agent reply: Hey, that doesn't sound good! Did the app crash at any point during the 30 minutes? That can cause the ad-free time to reset
  - brand reply: Hi Fran! We've just sent a DM your way. Let's carry on chatting there
  - judge: Asserts a specific, unverified technical claim (that app crashes reset ad-free time) rather than gathering more information about an ambiguous tweet.
- **I have just sent a DM regarding an issue from yesterday/today**
  - gold: dm_status_followup / ESC:repeat_contact · agent: dm_status_followup (0.95) / ESC:repeat_contact
  - agent reply: Hey there! We've just replied to your DM. Check it out
  - brand reply: Hi Elle! We've just sent you a bit more info over DM. We'll carry on helping out there
  - judge: Falsely claims 'we've just replied to your DM,' an unverified action claim the rubric explicitly flags as unsafe.
- **is there any way of me figuring out who appeared on The Indie List playlist last week? i didnt download it and fell in love with so many songs and now cant find them anywhere 😅**
  - gold: how_to_usage / auto · agent: how_to_usage (0.90) / auto
  - agent reply: Hi there! It's currently not possible to view who's on a playlist, but we can see how that'd be useful. Thanks for the feedback 🙂
  - brand reply: Hey Tayla! Unfortunately we're unable to recover last week's The Indie Playlist. Be sure to save your favorites, so you don't miss out in the future. For anything else, just give us a shout ✌️
  - judge: Misreads the request as wanting to view playlist contributors in general, rather than trying to recover last week's specific playlist as the customer actually asked.

### Fails `correct_next_step`

- **On the iphone app the artist page needs to be in alpha order like it is on the ipad. Right now it is a jumbled mess.**
  - gold: feedback_feature_request / auto · agent: feedback_feature_request (0.90) / auto
  - agent reply: Hey! Thanks for the feedback. We can see how that'd be useful. You can vote for the idea here: [link] 🙂
  - brand reply: Hey Rob, help's here! Could you send us a screenshot of what it looks like on your iPhone? We'll take a look
  - judge: Treats an inconsistency the customer says already exists on iPad as an unreleased feature idea, misrepresenting the issue instead of investigating it like the reference did.
- **I listen to mostly podcasts but will test with music today. Does the same when not using Bluetooth and just playing through phone speakers.** _(after: Just to check, does this happen only to podcasts, and music plays fine? Also, is the playb)_
  - gold: technical_issue / ESC:troubleshooting_exhausted · agent: technical_issue (0.95) / ESC:troubleshooting_exhausted
  - agent reply: Thanks for testing that. Can you DM us your account's email address or username? We'll take a look backstage [link]
  - brand reply: Got it. Loop us in how it goes when you've tested with your songs. We'll be right here for your update
  - judge: Skips ahead to requesting account details via DM instead of waiting for the music playback test the customer said they would run next.
- **Seems to be affected by my Bluetooth headphones. No issues if I play using my phone's speakers** _(after: That's odd. Can you let us know if this happens over WiFi and/or 4G? We'll be on the looko)_
  - gold: technical_issue / ESC:troubleshooting_exhausted · agent: technical_issue (0.95) / auto
  - agent reply: Got it. For now, we'd recommend using a different headset. Let us know if that helps
  - brand reply: Thanks for letting us know. Do you notice this issue happening with other apps? Also, does restarting your phone help at all?
  - judge: Jumps to recommending a hardware workaround instead of continuing the diagnostic questioning (e.g., testing across other apps) the reference used to isolate the cause.
- **Headphones work fine on all other devices and desktop player of this computer works fine w/o headphones.** _(after: Hmm, that's odd. Is the issue only happening when using your specific computer? Have you t)_
  - gold: technical_issue / auto · agent: technical_issue (0.95) / ESC:troubleshooting_exhausted
  - agent reply: Thanks for testing that. Can you DM us your account's email address or username? We'll take a look backstage [link]
  - brand reply: Do you have any other headphones to try on the computer that you're having issues with? If so, are you getting the same static issue?
  - judge: Falls back to generic account-DM boilerplate instead of continuing the headphone/hardware diagnostic already underway in the thread.
- **also down for me. Nothing loads except playlists.** _(after: Hey. Our best tech folks are on the case as we speak. Hopefully we'll have a fix soon!)_
  - gold: technical_issue / auto · agent: technical_issue (0.90) / auto
  - agent reply: Thanks for keeping us in the loop. Does logging out, restarting your device, and logging back in help? We're looking into this
  - brand reply: Hi there, thanks for bearing with us. Spotify should be working perfectly again!
  - judge: Asks the customer to try individual troubleshooting steps for what the thread already frames as a known platform-wide outage being handled backstage.

### Fails `tone`

- **do you actually understand? doing customer support of twitter only makes ppl like you if they feel that they won’t be ignored. if you’re working on new functionality for press & hold why take it out before you have the n** _(after: We understand. Thanks for taking the time to reach out – your feedback's been noted)_
  - gold: feedback_feature_request / auto · agent: feedback_feature_request (0.85) / auto
  - agent reply: We understand. Thanks for taking the time to reach out – your feedback's been noted
  - brand reply: Sorry you feel that way. We don't have any additional info to share about this right now, but rest assured we're passing on all comments about this to the right team
  - judge: Repeats verbatim the same boilerplate the customer already complained about being fobbed off with, ignoring their specific new frustration.
- **Truly appreciate the boiler plate response on how you plan to reintroduce basic features you once had 🙄** _(after: We can see how that’d be handy. Thanks for taking the time to reach out – your feedback's )_
  - gold: feedback_feature_request / auto · agent: feedback_feature_request (0.85) / auto
  - agent reply: Thanks for the feedback! We hear you. Anything else we can help with today?
  - brand reply: Sorry you feel that way. Lyrics is currently unavailable as we're making some big improvements to the feature. We'll share more updates soon. As for the inbox removal, we have some info about this her
  - judge: The customer just mocked receiving a canned response, and this draft replies with exactly that kind of generic boilerplate instead of the substantive explanation about lyrics and inbox removal that the reference gives.

### Fails `safe`

- **I have just sent a DM regarding an issue from yesterday/today**
  - gold: dm_status_followup / ESC:repeat_contact · agent: dm_status_followup (0.95) / ESC:repeat_contact
  - agent reply: Hey there! We've just replied to your DM. Check it out
  - brand reply: Hi Elle! We've just sent you a bit more info over DM. We'll carry on helping out there
  - judge: Falsely claims 'we've just replied to your DM,' an unverified action claim the rubric explicitly flags as unsafe.
- **[link]** _(after: Hi @user. I paid for Php 129 for a premium yesterday. I thought you have a promo Php 9 for)_
  - gold: billing_payment / ESC:billing · agent: billing_payment (0.70) / ESC:billing
  - agent reply: Can you DM us your account's email? We'll look into the pricing issue with you backstage [link]
  - brand reply: Hey there! We suggest deleting your screenshot as it contains private info. Can you send it over through DM instead? We'll take a look backstage
  - judge: Fails to flag that the customer's publicly posted screenshot may contain private payment info and advise deleting it, unlike the reference, leaving a privacy exposure unaddressed.
- **why have you charged me £14.99 for something I don’t even have or signed up too? I would like my money back! [link]**
  - gold: billing_payment / ESC:billing · agent: billing_payment (0.95) / ESC:billing
  - agent reply: Hi! We've just sent a DM your way. Let's carry on chatting there
  - brand reply: Hey! Help's here. Can you DM us your account's email address? We'll take a look backstage [link]
  - judge: Falsely claims a DM was already sent without ever collecting the account email needed to investigate the billing complaint.

## Guardrail triggers: none

Reply length: median 106, max 151
