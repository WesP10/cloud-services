import bcrypt

admin_hash = "$2b$12$Bsq66/d3TpJAm88m7pUDjOKt9d.zDWL//Ndo.M75MB8U.HUnf28Ue"
dev_hash = "$2b$12$3zeCNtJ3l7jPngfCu0ehsOEpr0.0nk2eInMVIXZNfVA5YVmRG5xG."

print(f"admin123 matches: {bcrypt.checkpw(b'admin123', admin_hash.encode())}")
print(f"dev123 matches: {bcrypt.checkpw(b'dev123', dev_hash.encode())}")
