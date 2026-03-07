# Licensing Strategy

## Recommended root license

This scaffold uses BSD-3-Clause for the core repository.

### Why
- permissive and common in scientific software
- compatible with broad adoption goals
- familiar to many imaging libraries

## Practical policy

- Keep the core repo permissive
- Keep backend adapters thin
- Avoid copying code from external projects unless licenses and attribution are handled explicitly
- Document dataset terms separately from code licenses

## GPL-sensitive integrations

Some valuable imaging backends use stronger copyleft licenses. The safest default is:

- keep wrappers optional
- document their license clearly
- if necessary, move the heaviest or most sensitive integrations to plugin packages

## Important reminder

Code license, dataset terms, and model weights terms may differ. Record them separately.
