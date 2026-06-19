# Checklist: changing a task status in Finkoper

Before changing the status of any task — go through this checklist.

## Moving a task to "In progress"

- [ ] The task text and all attachments have been read in full
- [ ] The client and task type are identified
- [ ] The client card is open
- [ ] The checklist for the task type is open (if there is one)
- [ ] The deadline is understood
- [ ] If data is needed — a request has been sent or scheduled
- [ ] A message "Took the task into work..." has been sent to the task chat

## Moving a task to "Waiting" (waiting for data / a decision)

- [ ] It's clear who we're waiting on (client / supervisor / counterparty / FTS)
- [ ] The request has been sent and recorded in `request_log.md`
- [ ] A message has been added to the task chat saying what we're waiting for and until what date
- [ ] A reminder is set for the repeat-request date (if there's no reply)

## Moving a task to "For review" (if such a status exists)

- [ ] All checklist steps have been completed
- [ ] The result is prepared and verified
- [ ] Files are attached / the result is posted to the task chat
- [ ] A message "Done, please review" has been added to the chat

## Moving a task to "Closed"

- [ ] The result has been sent / the task is complete
- [ ] The client / supervisor has confirmed acceptance
- [ ] The client's `history.md` is updated (an entry per the template)
- [ ] The registries are updated if applicable (`request_log`, `reporting_archive`)
- [ ] The JSON is updated if applicable, the dashboard regenerated
- [ ] A final message has been added to the task chat

## What NOT to do

- Don't close a task without confirmation from whoever set it
- Don't close it "to make the stats look nice" if the work isn't actually finished
- Don't move it to "Waiting" if you're really just procrastinating — better to honestly show that the task is hanging
