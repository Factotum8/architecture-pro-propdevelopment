python3 audit_filter.py audit.log --secrets-get > audit-extract.json
python3 audit_filter.py audit.log --create-exec > audit-extract.json
python3 audit_filter.py audit.log --privileged-pods > audit-extract.json
python3 audit_filter.py audit.log --grep audit-policy > audit-extract.json
