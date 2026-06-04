# Extract Reviewer Map

Build a reviewer coverage map from reviews and response anchors.

For each reviewer, output:

`id`: anonymized reviewer ID.

`stance`: concise stance summary.

`covered`: boolean.

`coverage`: integer 0-100 based on visible response anchors.

`concerns`: 2-5 concern labels.

`anchors`: dashboard issue IDs that address this reviewer.

Coverage means each important concern has a visible response anchor. It does not mean the response is persuasive or accepted.
