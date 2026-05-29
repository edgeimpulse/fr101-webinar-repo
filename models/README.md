# Models

Large model files are intentionally excluded from Git and from this zip.

Copy these to the FR101:

```bash
/home/onlogic/webinar/models/fomo_ad_cpu.eim   # Linux AARCH64 non-QNN fallback
/home/onlogic/webinar/models/fomo_ad_qnn.eim   # Linux AARCH64 with Qualcomm QNN
```

Make them executable:

```bash
chmod +x /home/onlogic/webinar/models/*.eim
```

The CPU model is the reliable live path. The QNN model needs `qairt-env.sh` sourced first.
