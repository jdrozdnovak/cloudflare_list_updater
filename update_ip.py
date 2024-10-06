import requests
import os

# Cloudflare API details
CLOUDFLARE_API_EMAIL = os.getenv("CLOUDFLARE_API_EMAIL")
CLOUDFLARE_API_KEY = os.getenv("CLOUDFLARE_API_KEY")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
LIST_ID = os.getenv("LIST_ID")
COMMENT = os.getenv("COMMENT")

# API endpoints
CLOUDFLARE_LIST_API_URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/rules/lists/{LIST_ID}/items"
PUBLIC_IP_API = "https://ifconfig.me"

# Cloudflare authentication headers using X-Auth-Email and X-Auth-Key
headers = {
    "X-Auth-Email": CLOUDFLARE_API_EMAIL,
    "X-Auth-Key": CLOUDFLARE_API_KEY,
    "Content-Type": "application/json",
}

def get_public_ip() -> str:
    try:
        response = requests.get(PUBLIC_IP_API)
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException as e:
        print(f"Error getting public IP: {e}")
        return None

def update_cloudflare_list(ip: str) -> None:
    try:
        # Get the current list entries from Cloudflare
        response = requests.get(CLOUDFLARE_LIST_API_URL, headers=headers)
        response.raise_for_status()
        items = response.json().get('result', [])

        # Find the entry to update (based on comment)
        for item in items:
            if item['comment'] == COMMENT:
                item_id = item['id']

                # Delete the old entry using the DELETE method
                delete_url = f"{CLOUDFLARE_LIST_API_URL}/{item_id}"
                delete_response = requests.delete(delete_url, headers=headers)
                delete_response.raise_for_status()
                print(f"Deleted old entry with IP: {item['content']}")

                # Add the new entry with the updated IP
                add_payload = [{
                    "content": ip,
                    "comment": COMMENT
                }]
                add_response = requests.post(CLOUDFLARE_LIST_API_URL, headers=headers, json=add_payload)
                add_response.raise_for_status()
                print(f"Added new entry with IP: {ip}")
                return

    except requests.RequestException as e:
        print(f"Error updating Cloudflare list: {e}")

def main():
    current_ip = get_public_ip()
    if current_ip:
        print(f"Current IP: {current_ip}, updating Cloudflare...")
        update_cloudflare_list(current_ip)
    else:
        print("Failed to retrieve the public IP.")

if __name__ == "__main__":
    main()
