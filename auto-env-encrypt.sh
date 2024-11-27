#!/bin/bash

# Prompt user for passphrase
read -s -p "Enter passphrase for encryption/decryption: " ENV_PASSPHRASE
echo

# Directory for hooks
HOOKS_DIR=".git/hooks"

# Create pre-commit hook
cat <<EOL > "$HOOKS_DIR/pre-commit"
#!/bin/bash
ENV_FILE=".env"
ENV_GPG_FILE=".env.gpg"
ENV_PASSPHRASE="$ENV_PASSPHRASE"

if [ -f "\$ENV_FILE" ]; then
    gpg --batch --passphrase "\$ENV_PASSPHRASE" -c "\$ENV_FILE"
    git add "\$ENV_GPG_FILE"
fi
EOL

# Create post-merge hook
cat <<EOL > "$HOOKS_DIR/post-merge"
#!/bin/bash
ENV_GPG_FILE=".env.gpg"
ENV_FILE=".env"
ENV_PASSPHRASE="$ENV_PASSPHRASE"

if [ -f "\$ENV_GPG_FILE" ]; then
    gpg --batch --passphrase "\$ENV_PASSPHRASE" -d "\$ENV_GPG_FILE" > "\$ENV_FILE"
fi
EOL

# Create post-checkout hook
cat <<EOL > "$HOOKS_DIR/post-checkout"
#!/bin/bash
ENV_GPG_FILE=".env.gpg"
ENV_FILE=".env"
ENV_PASSPHRASE="$ENV_PASSPHRASE"

if [ -f "\$ENV_GPG_FILE" ]; then
    gpg --batch --passphrase "\$ENV_PASSPHRASE" -d "\$ENV_GPG_FILE" > "\$ENV_FILE"
fi
EOL

# Make hooks executable
chmod +x "$HOOKS_DIR/pre-commit" "$HOOKS_DIR/post-merge" "$HOOKS_DIR/post-checkout"

echo "Git hooks for .env encryption and decryption have been set up."
