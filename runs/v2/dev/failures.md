# Failure analysis — v2 / dev

## Intent confusions (39 errors / 250)

- gold **technical_issue** → predicted **account_access**: 4
- gold **subscription_plan** → predicted **billing_payment**: 3
- gold **how_to_usage** → predicted **subscription_plan**: 3
- gold **billing_payment** → predicted **account_access**: 3
- gold **technical_issue** → predicted **other**: 3
- gold **other** → predicted **technical_issue**: 2
- gold **how_to_usage** → predicted **feedback_feature_request**: 2
- gold **billing_payment** → predicted **subscription_plan**: 2
- gold **technical_issue** → predicted **feedback_feature_request**: 2
- gold **other** → predicted **account_access**: 1
- gold **technical_issue** → predicted **billing_payment**: 1
- gold **how_to_usage** → predicted **technical_issue**: 1

### technical_issue → account_access

- **Another day, another device @user randomly connects to and plays randomly chosen music through. 🙄 How do I stop this from happening without constantly having to unconnect bluetooth? @user**
  - gold: technical_issue / auto · agent: account_access (0.90) / ESC:security
  - agent reply: Hey! We're sorry to hear that. Can you DM us your email address? We'll check backstage [link]
  - brand reply: Hey, that's not cool! Before anything else, can you DM us your account's email address or username? Knowing what device/version of Spotify you're using would also be helpful. Once we have this info, w
- **guess you're down**
  - gold: technical_issue / auto · agent: account_access (0.85) / auto
  - agent reply: Hey! Everything looks good on our end. Can you tell us what's happening exactly? [link]
  - brand reply: Hey there! Thanks for letting us know. Everything’s looking good on our end now - are you still having this issue?
- **Linking to Hulu does not work anymore. Help?**
  - gold: technical_issue / auto · agent: account_access (0.85) / ESC:account_specific
  - agent reply: Hey! Could you DM us your account's email address? We'll take a look backstage [link]
  - brand reply: Hey there, help's here! Can you DM us your account's username and email address? We'll take a look backstage [link]

### subscription_plan → billing_payment

- **Why can't my brother start his spotify premium for 0.99? It keeps telling him " This form has expired. Please reload the page and try again. " for some odd reason.**
  - gold: subscription_plan / auto · agent: billing_payment (0.91) / ESC:billing
  - agent reply: Hey there, help's here! Can you DM us your account's email or username? We'll take a look backstage [link]
  - brand reply: Hey there! Could you send us your brother's email address or username via DM? We'll take a look backstage [link]
- **. I accidentally subscribed to the Spotify Premium Free Trail while pressing on the mobile phone. Could you help me to unsubscribed to the free trial? I know it's free but I do not want to waste the free trial. My accoun**
  - gold: subscription_plan / ESC:account_specific · agent: billing_payment (0.92) / ESC:account_specific
  - agent reply: Hey! Can you DM us your account's email? We'll help you sort this out backstage [link]
  - brand reply: Hey Calvin. We suggest deleting your public post as it contains private info. Can you DM it to us instead? [link]
- **thanks for saying your gunna give me a month free and than take it away a week later. #notcool#likedtheservicetillthan**
  - gold: subscription_plan / ESC:account_specific · agent: billing_payment (0.89) / ESC:billing
  - agent reply: Hey! Can you DM us your account's email? We'll look into this backstage [link]
  - brand reply: Hey Jake! Can you DM us your account's email address or username? We'll take a look backstage [link]

### how_to_usage → subscription_plan

- **is it possible to get a discount on Spotify Premium for Family by paying for a whole year all at once?**
  - gold: how_to_usage / auto · agent: subscription_plan (0.89) / auto
  - agent reply: Hey! You can purchase Premium for 1 year at [link] > See more offers. Let us know if you have other questions!
  - brand reply: Hi Andy! Right now, it isn't possible to sign up for a full year of Premium for Family, but you can sign up for the Annual Discount then upgrade to Premium for Family. Note that this will move your re
- **How do I access a presale code for a concert? Presale begins 11/28. I have a “free” account. Thanks!**
  - gold: how_to_usage / auto · agent: subscription_plan (0.85) / auto
  - agent reply: Pre-sale codes are sent to some of the artist's biggest fans on Spotify. Hopefully you're one of them!
  - brand reply: Hey Sue! We've just replied to your DM. Check your Messages
- **When you have @user premium and follow @user, but haven’t gotten a presale code yet & tickets went on sale. Help?**
  - gold: how_to_usage / auto · agent: subscription_plan (0.85) / auto
  - agent reply: Pre-sale codes are sent to some of the artist's biggest fans on Spotify. Hopefully you'll get one!
  - brand reply: Hi! Pre-sale codes are being sent out by email to some of Betty Who's biggest fans on Spotify. Hopefully you're one of them

### billing_payment → account_access

- **Please check my spotify account i was asked to downgrade and im sure im on autopayment. @user**
  - gold: billing_payment / ESC:billing · agent: account_access (0.92) / ESC:account_specific
  - agent reply: Hey! We've just sent you a bit more info over DM. We'll carry on helping out there 🙂
  - brand reply: Hey Aldrinos, help's here. Could you DM us your account's email address and username? We'll take a look backstage [link]
- **hi i have sign up under premium but cant download anything, it require me to re-do it again pls help to check :)**
  - gold: billing_payment / ESC:account_specific · agent: account_access (0.95) / ESC:account_specific
  - agent reply: Hey there! Let's get Premium working for you. Could you DM us your account's email address or username? We'll take a look backstage [link]
  - brand reply: Hey there! Can you fire over your account's email address or username via DM? We'll see what we can suggest [link]
- **hey, my username is sinemergun. i bought premimum but i still don't use premium. please help**
  - gold: billing_payment / ESC:account_specific · agent: account_access (0.90) / ESC:account_specific
  - agent reply: Hey! Help's here. Could you DM us your account's username or email? We'll take a look [link]
  - brand reply: Hey, help's here! We've just replied to your DM. Let's carry on chatting there

## Missed escalations — auto-sent but should escalate (13)

By gold reason: troubleshooting_exhausted: 7, repeat_contact: 2, account_specific: 2, risk: 1, billing: 1
- **I have just sent a DM regarding an issue from yesterday/today**
  - gold: dm_status_followup / ESC:repeat_contact · agent: dm_status_followup (0.93) / auto
  - agent reply: Hey there! Can you DM us more info about what's happening? We'll see what we can suggest [link]
  - brand reply: Hi Elle! We've just sent you a bit more info over DM. We'll carry on helping out there
- **Restarting my phone doesn't work, it's version 8.4. 28. 875** _(after: Hey there! Can you let us know which Android version you're using? Does restarting your ph)_
  - gold: technical_issue / ESC:troubleshooting_exhausted · agent: technical_issue (0.88) / auto
  - agent reply: Thanks for trying that! Can you try a reinstall? Follow the steps at [link] and let us know how it plays out
  - brand reply: Thanks. Can we have you try the steps here for us: [link] They should help with this. Let us know how it goes
- **It's a Samsung. Thanks. I just get this screen [link]** _(after: Hey Stephanie, help's here! What’s happening exactly? Can you let us know the device/OS yo)_
  - gold: technical_issue / ESC:troubleshooting_exhausted · agent: technical_issue (0.85) / auto
  - agent reply: Thanks for the screenshot! What does the error message say? That'll help us figure it out
  - brand reply: Hmm. What happens when you tap on any of the icons below? Try logging out > restarting your phone > then logging back in again. Can you also DM us your account's email address? We'll take a look under
- **can you help us with this? Our music is getting grouped in with the wrong artist with the same name, and @user has been zero help 🙏🏼🙏🏼🙏🏼🙏🏼🙏🏼🙏🏼 [link]**
  - gold: artist_creator / ESC:repeat_contact · agent: artist_creator (0.92) / auto
  - agent reply: Hey! Can you send us the Artist Links? Just tap three dots > Share > Copy Link. We'll take a look
  - brand reply: Hey - sorry about that! We’d recommend reaching out to your distributor/aggregator. They'll work with our team to make sure your artist page gets fixed up
- **Sure! It’s [link] PS.: pay attention because this song is also in other albuns of the same band, so remember to check if the title is correct in all of them! 💕** _(after: Hey! The cavalry's here. Can you send us the Song Link? Just tap the three dots > Share > )_
  - gold: artist_creator / ESC:account_specific · agent: artist_creator (0.89) / auto
  - agent reply: Thanks for the heads-up! We'll report this to our Content team. Great detective work! [link]
  - brand reply: Thanks. We'll get this reported. Great detective work! [link]
- **Hi @user today i can't open Spotify on my computer (windows 8) I get this message : "Cannot find 'api-ms-win-core-processthreads-l1-1-12.dll'. Please re-install this application." I can't uninstall Spotify, it shows the **
  - gold: technical_issue / ESC:troubleshooting_exhausted · agent: technical_issue (0.95) / auto
  - agent reply: Can you try deleting all Spotify folders on your device, then reinstall the app? Let us know how it goes
  - brand reply: Hey! Does restarting the device help at all? Let us know how it goes
- **I received a notification on your annual premium subscription but logged in and can’t find how I can take advantage of this**
  - gold: subscription_plan / ESC:account_specific · agent: subscription_plan (0.85) / auto
  - agent reply: Can you tell us more about the notification you received? That'll help us point you in the right direction 🙂
  - brand reply: Hey, help's here! Can you DM us your account's email address along with a screenshot of the page you're seeing when you clicked on the emailed link for the offer? We'll take a closer look [link]
- **Wi-Fi. Restarting my phone made no difference.** _(after: Got it! Is this happening on 3G/4G, WiFi, or both? Does restarting your phone make any dif)_
  - gold: technical_issue / ESC:troubleshooting_exhausted · agent: technical_issue (0.90) / auto
  - agent reply: Got it. Best thing to try here is a reinstall. Just follow the steps at [link] Let us know how it goes
  - brand reply: Hmm. Can you DM us your account's email address? We'll take a look under the hood [link]

## Needless escalations (24)

By agent reason: account_specific: 11, troubleshooting_exhausted: 9, security: 2, billing: 1, repeat_contact: 1
- **I listen to mostly podcasts but will test with music today. Does the same when not using Bluetooth and just playing through phone speakers.** _(after: Just to check, does this happen only to podcasts, and music plays fine? Also, is the playb)_
  - gold: technical_issue / auto · agent: technical_issue (0.91) / ESC:troubleshooting_exhausted
  - agent reply: Got it. Could you DM us your account's email address? We'll check things out backstage [link]
  - brand reply: Got it. Loop us in how it goes when you've tested with your songs. We'll be right here for your update
  - agent reason: Customer exhausted standard fixes; needs deeper investigation.
- **Seems to be affected by my Bluetooth headphones. No issues if I play using my phone's speakers** _(after: That's odd. Can you let us know if this happens over WiFi and/or 4G? We'll be on the looko)_
  - gold: technical_issue / auto · agent: technical_issue (0.89) / ESC:troubleshooting_exhausted
  - agent reply: Got it. Could you DM us your account's email address? We'll take a closer look backstage [link]
  - brand reply: Thanks for letting us know. Do you notice this issue happening with other apps? Also, does restarting your phone help at all?
  - agent reason: Issue isolated to Bluetooth but persists after troubleshooting.
- **Headphones work fine on all other devices and desktop player of this computer works fine w/o headphones.** _(after: Hmm, that's odd. Is the issue only happening when using your specific computer? Have you t)_
  - gold: technical_issue / auto · agent: technical_issue (0.88) / ESC:troubleshooting_exhausted
  - agent reply: Hmm. Could you DM us your account's email address? We'll take a look backstage [link]
  - brand reply: Do you have any other headphones to try on the computer that you're having issues with? If so, are you getting the same static issue?
  - agent reason: Issue isolated but unresolved after extensive troubleshooting.
- **sort your shit out man don’t have premium for you to not even let me on the app**
  - gold: technical_issue / auto · agent: technical_issue (0.83) / ESC:account_specific
  - agent reply: Hey! Help's here. Can you DM us your account's email address? We'll take a look backstage [link]
  - brand reply: Hey Lewis! Everything should be running smoothly now. Let us know if this is still happening
  - agent reason: Premium not working post-payment; account verification needed.
- **Why can't my brother start his spotify premium for 0.99? It keeps telling him " This form has expired. Please reload the page and try again. " for some odd reason.**
  - gold: subscription_plan / auto · agent: billing_payment (0.91) / ESC:billing
  - agent reply: Hey there, help's here! Can you DM us your account's email or username? We'll take a look backstage [link]
  - brand reply: Hey there! Could you send us your brother's email address or username via DM? We'll take a look backstage [link]
  - agent reason: Payment form expiring; billing issue requiring account check.
- **hi @user, if im a premium account holder and want to subscribe a premium for family account, do i have to terminate my earlier account? or i can just subscribe for the premium for family?**
  - gold: subscription_plan / auto · agent: subscription_plan (0.87) / ESC:account_specific
  - agent reply: Hey! Can you DM us your account's email or username? We'll help you upgrade [link]
  - brand reply: Hey, help's here! Can you DM us your account's username or email address? We'll take a look under the hood [link]
  - agent reason: Family plan upgrade requires account verification.
- **net een premium account omgezet in Family account. Hoe kan ik mijn dochter, die nog geen account heeft, toevoegen? Ze heeft wel de mail ontvangen met de uitnodigingcode... #help #premiumforfamily #spotify #spotifynederla**
  - gold: subscription_plan / auto · agent: subscription_plan (0.92) / ESC:account_specific
  - agent reply: Hoi! Stuur ons je accountgegevens via DM, we helpen je graag met je Family plan 🎵
  - brand reply: Hey there! We can help out in English via Twitter, but we also have Dutch support via email at [link] 🙂
  - agent reason: Family plan member setup requires account verification and troubleshooting.
- **No it's back down again. That dll. is missing again after a reboot of my computer. It's a bad problem.** _(after: Hey! Nice one, glad you're all fixed up and back to your tunes. If you ever need anything )_
  - gold: technical_issue / auto · agent: technical_issue (0.88) / ESC:troubleshooting_exhausted
  - agent reply: We understand the frustration. Can you DM us your email? We'll investigate further [link]
  - brand reply: Oh no, that's a shame. Can you DM us your account's email and send over a screenshot of the error you're seeing? We'll check things out behind the scenes and work to get this fixed up for you [link]
  - agent reason: Customer reports DLL issue persists after restart and multiple fix attempts.

## Reply failures by rubric criterion (250 judged)

- addresses_issue: 36 fails (14%)
- grounded: 28 fails (11%)
- correct_next_step: 61 fails (24%)
- tone: 3 fails (1%)
- safe: 6 fails (2%)
- would_send: 65 fails (26%)

### Fails `addresses_issue`

- **Headphones work fine on all other devices and desktop player of this computer works fine w/o headphones.** _(after: Hmm, that's odd. Is the issue only happening when using your specific computer? Have you t)_
  - gold: technical_issue / auto · agent: technical_issue (0.88) / ESC:troubleshooting_exhausted
  - agent reply: Hmm. Could you DM us your account's email address? We'll take a look backstage [link]
  - brand reply: Do you have any other headphones to try on the computer that you're having issues with? If so, are you getting the same static issue?
  - judge: Ignores the isolated hardware/static troubleshooting thread and pivots to a generic account DM request instead of the next diagnostic question.
- **also down for me. Nothing loads except playlists.** _(after: Hey. Our best tech folks are on the case as we speak. Hopefully we'll have a fix soon!)_
  - gold: technical_issue / auto · agent: technical_issue (0.86) / auto
  - agent reply: That's odd. What device, operating system, and Spotify version are you using? Does restarting help?
  - brand reply: Hi there, thanks for bearing with us. Spotify should be working perfectly again!
  - judge: Ignores that the team already acknowledged a known outage and asks basic device questions again, sending the customer in circles.
- **I have just sent a DM regarding an issue from yesterday/today**
  - gold: dm_status_followup / ESC:repeat_contact · agent: dm_status_followup (0.93) / auto
  - agent reply: Hey there! Can you DM us more info about what's happening? We'll see what we can suggest [link]
  - brand reply: Hi Elle! We've just sent you a bit more info over DM. We'll carry on helping out there
  - judge: Ignores that the customer already said they sent a DM and asks them to DM again as if starting over.
- **is it possible to get a discount on Spotify Premium for Family by paying for a whole year all at once?**
  - gold: how_to_usage / auto · agent: subscription_plan (0.89) / auto
  - agent reply: Hey! You can purchase Premium for 1 year at [link] > See more offers. Let us know if you have other questions!
  - brand reply: Hi Andy! Right now, it isn't possible to sign up for a full year of Premium for Family, but you can sign up for the Annual Discount then upgrade to Premium for Family. Note that this will move your re
  - judge: Implies a direct annual discount is available for Premium for Family when the reference makes clear this isn't directly possible and requires a specific workaround.
- **first off, you are very late. i messaged you over an 30 minuets ago; very disappointing. anyways, my question is how did the picture change? is this some sort of secret witchcraft you have? i need answers & i need them n** _(after: Hey Ky, thanks for reaching out. What’s happening exactly? We'd be happy to help)_
  - gold: technical_issue / auto · agent: technical_issue (0.86) / ESC:repeat_contact
  - agent reply: We've just replied to your DM with more info. We'll carry on helping there
  - brand reply: We understand your frustration. The picture changed because when you open the artist display photo it routes you to their bio photo. If you ever need anything else, just shout and we'll come running 🏃
  - judge: The draft falsely claims a DM reply was already sent instead of actually explaining why the picture changed.

### Fails `grounded`

- **" Enjoy 30 minutes of add free music " [link]**
  - gold: other / auto · agent: technical_issue (0.81) / auto
  - agent reply: That doesn't sound good! Did the app crash at any point? That can cause ad-free time to reset
  - brand reply: Hi Fran! We've just sent a DM your way. Let's carry on chatting there
  - judge: Invents an unverified causal claim about app crashes resetting ad-free time rather than following up for more detail as the reference did.
- **is it possible to get a discount on Spotify Premium for Family by paying for a whole year all at once?**
  - gold: how_to_usage / auto · agent: subscription_plan (0.89) / auto
  - agent reply: Hey! You can purchase Premium for 1 year at [link] > See more offers. Let us know if you have other questions!
  - brand reply: Hi Andy! Right now, it isn't possible to sign up for a full year of Premium for Family, but you can sign up for the Annual Discount then upgrade to Premium for Family. Note that this will move your re
  - judge: Implies a direct annual discount is available for Premium for Family when the reference makes clear this isn't directly possible and requires a specific workaround.
- **net een premium account omgezet in Family account. Hoe kan ik mijn dochter, die nog geen account heeft, toevoegen? Ze heeft wel de mail ontvangen met de uitnodigingcode... #help #premiumforfamily #spotify #spotifynederla**
  - gold: subscription_plan / auto · agent: subscription_plan (0.92) / ESC:account_specific
  - agent reply: Hoi! Stuur ons je accountgegevens via DM, we helpen je graag met je Family plan 🎵
  - brand reply: Hey there! We can help out in English via Twitter, but we also have Dutch support via email at [link] 🙂
  - judge: Offers to handle the request directly in Dutch over DM, contradicting the reference's indication that Dutch support is only available via email, not Twitter.
- **can you help us with this? Our music is getting grouped in with the wrong artist with the same name, and @user has been zero help 🙏🏼🙏🏼🙏🏼🙏🏼🙏🏼🙏🏼 [link]**
  - gold: artist_creator / ESC:repeat_contact · agent: artist_creator (0.92) / auto
  - agent reply: Hey! Can you send us the Artist Links? Just tap three dots > Share > Copy Link. We'll take a look
  - brand reply: Hey - sorry about that! We’d recommend reaching out to your distributor/aggregator. They'll work with our team to make sure your artist page gets fixed up
  - judge: Offers to personally fix the artist page mix-up when the reference makes clear this must go through the distributor/aggregator, not SpotifyCares directly.
- **are you aware of the iPhone X / iOS11 bug wherein if a video plays in another app it stops all audio coming from your app? Have to restart each time.**
  - gold: technical_issue / auto · agent: technical_issue (0.88) / auto
  - agent reply: Hey Ben! Can you let us know your phone's iOS and Spotify versions? We'll see what we can suggest
  - brand reply: Hi there. Just to clarify, do you need to restart the app to continue your music, or do you just resume the playback?
  - judge: Invents a customer name (Ben) not present anywhere in the given context.

### Fails `correct_next_step`

- **I listen to mostly podcasts but will test with music today. Does the same when not using Bluetooth and just playing through phone speakers.** _(after: Just to check, does this happen only to podcasts, and music plays fine? Also, is the playb)_
  - gold: technical_issue / auto · agent: technical_issue (0.91) / ESC:troubleshooting_exhausted
  - agent reply: Got it. Could you DM us your account's email address? We'll check things out backstage [link]
  - brand reply: Got it. Loop us in how it goes when you've tested with your songs. We'll be right here for your update
  - judge: Skips the pending step of waiting for the music-playback test the rep already asked for and jumps prematurely to an account lookup.
- **Seems to be affected by my Bluetooth headphones. No issues if I play using my phone's speakers** _(after: That's odd. Can you let us know if this happens over WiFi and/or 4G? We'll be on the looko)_
  - gold: technical_issue / auto · agent: technical_issue (0.89) / ESC:troubleshooting_exhausted
  - agent reply: Got it. Could you DM us your account's email address? We'll take a closer look backstage [link]
  - brand reply: Thanks for letting us know. Do you notice this issue happening with other apps? Also, does restarting your phone help at all?
  - judge: Jumps to an account DM request when the evidence points to a Bluetooth/device issue rather than an account problem.
- **Headphones work fine on all other devices and desktop player of this computer works fine w/o headphones.** _(after: Hmm, that's odd. Is the issue only happening when using your specific computer? Have you t)_
  - gold: technical_issue / auto · agent: technical_issue (0.88) / ESC:troubleshooting_exhausted
  - agent reply: Hmm. Could you DM us your account's email address? We'll take a look backstage [link]
  - brand reply: Do you have any other headphones to try on the computer that you're having issues with? If so, are you getting the same static issue?
  - judge: Ignores the isolated hardware/static troubleshooting thread and pivots to a generic account DM request instead of the next diagnostic question.
- **also down for me. Nothing loads except playlists.** _(after: Hey. Our best tech folks are on the case as we speak. Hopefully we'll have a fix soon!)_
  - gold: technical_issue / auto · agent: technical_issue (0.86) / auto
  - agent reply: That's odd. What device, operating system, and Spotify version are you using? Does restarting help?
  - brand reply: Hi there, thanks for bearing with us. Spotify should be working perfectly again!
  - judge: Ignores that the team already acknowledged a known outage and asks basic device questions again, sending the customer in circles.
- **" Enjoy 30 minutes of add free music " [link]**
  - gold: other / auto · agent: technical_issue (0.81) / auto
  - agent reply: That doesn't sound good! Did the app crash at any point? That can cause ad-free time to reset
  - brand reply: Hi Fran! We've just sent a DM your way. Let's carry on chatting there
  - judge: Invents an unverified causal claim about app crashes resetting ad-free time rather than following up for more detail as the reference did.

### Fails `tone`

- **My playlist was depressing as heck, u made me upset** _(after: Hey Vladimir, help's here! What's happening exactly? Let us know and we'll see what we can)_
  - gold: feedback_feature_request / auto · agent: feedback_feature_request (0.90) / auto
  - agent reply: Only you control your playlists - we just suggest songs based on what you listen to. Let us know if there's anything else!
  - brand reply: Sorry to hear Discover Weekly wasn’t to your liking this week. Don't worry, it’ll be re-tuned on Monday. In the meantime, just keep listening to your favorite tunes to improve the mix. Let us know if 
  - judge: The customer said the playlist upset them, but the draft skips any empathy or reassurance (like the reference's 'it'll be re-tuned Monday') and reads as slightly dismissive.
- **do you actually understand? doing customer support of twitter only makes ppl like you if they feel that they won’t be ignored. if you’re working on new functionality for press & hold why take it out before you have the n** _(after: We understand. Thanks for taking the time to reach out – your feedback's been noted)_
  - gold: feedback_feature_request / auto · agent: feedback_feature_request (0.80) / auto
  - agent reply: We understand your feedback. We're here to help on Twitter! What can we assist with?
  - brand reply: Sorry you feel that way. We don't have any additional info to share about this right now, but rest assured we're passing on all comments about this to the right team
  - judge: Draft responds with generic, chipper boilerplate that ignores the customer's specific frustration about poor communication, coming across as dismissive rather than empathetic.
- **Truly appreciate the boiler plate response on how you plan to reintroduce basic features you once had 🙄** _(after: We can see how that’d be handy. Thanks for taking the time to reach out – your feedback's )_
  - gold: feedback_feature_request / auto · agent: feedback_feature_request (0.80) / auto
  - agent reply: We appreciate your feedback on that! We're always looking to improve our experience 📝
  - brand reply: Sorry you feel that way. Lyrics is currently unavailable as we're making some big improvements to the feature. We'll share more updates soon. As for the inbox removal, we have some info about this her
  - judge: Draft repeats generic boilerplate language despite the customer explicitly calling out boilerplate responses, failing to provide the specific lyrics and inbox information the reference gives.

### Fails `safe`

- **first off, you are very late. i messaged you over an 30 minuets ago; very disappointing. anyways, my question is how did the picture change? is this some sort of secret witchcraft you have? i need answers & i need them n** _(after: Hey Ky, thanks for reaching out. What’s happening exactly? We'd be happy to help)_
  - gold: technical_issue / auto · agent: technical_issue (0.86) / ESC:repeat_contact
  - agent reply: We've just replied to your DM with more info. We'll carry on helping there
  - brand reply: We understand your frustration. The picture changed because when you open the artist display photo it routes you to their bio photo. If you ever need anything else, just shout and we'll come running 🏃
  - judge: The draft falsely claims a DM reply was already sent instead of actually explaining why the picture changed.
- **Hi can't update payment info with new payment method. Tried canceling account and that didn't work either. HELP!**
  - gold: billing_payment / ESC:account_specific · agent: billing_payment (0.88) / ESC:billing
  - agent reply: Hey! We've just sent you a bit more info over DM. We'll carry on helping out there 🙂
  - brand reply: Hey Spencer, help's here. Can you DM us your account's email address and username? We'll take a look backstage [link]
  - judge: The draft falsely claims a DM was already sent instead of actually requesting the account info needed to help with the payment issue.
- **Please check my spotify account i was asked to downgrade and im sure im on autopayment. @user**
  - gold: billing_payment / ESC:billing · agent: account_access (0.92) / ESC:account_specific
  - agent reply: Hey! We've just sent you a bit more info over DM. We'll carry on helping out there 🙂
  - brand reply: Hey Aldrinos, help's here. Could you DM us your account's email address and username? We'll take a look backstage [link]
  - judge: The draft falsely claims a DM was already sent instead of actually requesting the account info needed to check the downgrade/billing issue.
- **check dm**
  - gold: dm_status_followup / ESC:repeat_contact · agent: dm_status_followup (0.95) / ESC:repeat_contact
  - agent reply: We've already replied to your DM. Let's continue chatting there 🙂
  - brand reply: Hi Burch! We've just sent you a bit more info over DM. We'll carry on helping out there
  - judge: Asserts 'we've already replied to your DM,' an unverifiable claim of a prior action that the system prompt explicitly flags as unsafe.
- **Sorry, that's frustration more than anything. But yes. I listen mostly on my iOS device, and frequently notice patterns like that when shuffling. I am not kidding when I say shuffle played an ENTIRE album almost in a row** _(after: Hey there! That's not cool. Can you let us know if this is happening while using Spotify C)_
  - gold: technical_issue / auto · agent: feedback_feature_request (0.85) / auto
  - agent reply: We've made improvements to our shuffle algorithm. Share your feedback here: [link]
  - brand reply: Thanks for the report. The right team are aware of this issue between Shuffle and Connect and they're investigating
  - judge: Draft falsely claims shuffle algorithm improvements have already shipped, contradicting the reference's status of an ongoing investigation.

## Guardrail triggers: none

Reply length: median 91, max 138
