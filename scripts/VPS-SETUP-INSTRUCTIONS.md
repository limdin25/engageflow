# VPS Setup: Legacy + Main + Dev

## What You Need

1. **SSH access** to your VPS
2. **Password** for `ubuntu` user
3. **5 minutes**

---

## Step 1: SSH into the VPS

On your Mac, open Terminal and run:

```bash
ssh ubuntu@54.38.215.57
```

Enter your password when prompted.

---

## Step 2: Find where EngageFlow is

On the VPS, run:

```bash
find /var/www /home/ubuntu -name "docker-compose.yml" 2>/dev/null
```

Or:

```bash
ls -la /var/www/
```

Note the path (e.g. `/var/www/engageflow` or `/home/ubuntu/engageflow`).

---

## Step 3: Get the setup script onto the VPS

**Option A — Clone the repo (if EngageFlow isn't in git yet):**

```bash
cd /tmp
git clone https://github.com/limdin25/engageflow.git
cd engageflow
git fetch origin fix/profile-rotation-auth-timing-activity-feed
```

**Option B — If EngageFlow already exists:**

```bash
cd /var/www/engageflow   # or wherever you found it
```

---

## Step 4: Run the setup script

**If you cloned in /tmp:**

```bash
cd /tmp/engageflow
chmod +x scripts/vps-setup-legacy-main-dev.sh
./scripts/vps-setup-legacy-main-dev.sh
```

**If your EngageFlow is elsewhere:**

Copy the script content to the VPS, save as `setup.sh`, then:

```bash
chmod +x setup.sh
./setup.sh
```

---

## Step 5: Restart services

After the script finishes:

```bash
cd /var/www/engageflow
docker compose down
docker compose up -d
```

---

## Result

| Name   | Path                    | Purpose                |
|--------|-------------------------|------------------------|
| Legacy | git branch only         | Backup of old code     |
| Main   | `/var/www/engageflow/`   | Live site (port 80)    |
| Dev    | `/var/www/engageflow-dev/` | Test site (port 3001) |

---

## If SSH Fails

- Confirm the IP: `54.38.215.57`
- Confirm the password (change it in OVH if needed)
- Check the OVH firewall allows SSH (port 22)
