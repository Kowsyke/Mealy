# Mealy — Documentation Index

| File | Contents |
|------|----------|
| `UPDATE_JOURNAL.md` | Full development history from v0.1 setup to v1.0 live deployment |
| `PROJECT_PLAN.md` | Original project plan and stage breakdown |
| `mealy_project_guide.docx` | 16-step teacher guide: how everything was built and why |
| `generate_guide.py` | Python script that generated mealy_project_guide.docx |

## Live deployment

**Public URL:** https://56-228-34-22.sslip.io/mealy/

**Via Kowsite:** https://56-228-34-22.sslip.io → click MEALY in the sidebar

## Architecture summary

```
Browser → HTTPS (443) → EC2 nginx → /mealy/ → SSH tunnel → Fedora Flask (5001) → TensorFlow
```

All services auto-start on Fedora login via systemd user units.
