import requests
import os
import logging

# Set up logging
logging_level = logging.DEBUG if os.getenv("DEBUG", "false").lower() == "true" else logging.INFO
logging.basicConfig(level=logging_level, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudflareUpdater:
    def __init__(self, env_file="/etc/environment"):
        # Load environment variables from a file
        self.load_env_from_file(env_file)

        # Cloudflare API details
        self.cloudflare_api_email = os.getenv("CLOUDFLARE_API_EMAIL")
        self.cloudflare_api_key = os.getenv("CLOUDFLARE_API_KEY")
        self.account_id = os.getenv("ACCOUNT_ID")
        self.list_id = os.getenv("LIST_ID")
        self.comment = os.getenv("COMMENT")
        self.public_ip_api = "https://ifconfig.me"
        self.debug = os.getenv("DEBUG", "false").lower() == "true"

        # Cloudflare API endpoints
        self.cloudflare_list_api_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/rules/lists/{self.list_id}/items"

        # Cloudflare authentication headers using X-Auth-Email and X-Auth-Key
        self.headers = {
            "X-Auth-Email": self.cloudflare_api_email,
            "X-Auth-Key": self.cloudflare_api_key,
            "Content-Type": "application/json",
        }

    def load_env_from_file(self, env_file):
        """Load environment variables from a file into the OS environment."""
        try:
            with open(env_file, "r") as file:
                for line in file:
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value
                    logger.debug(f"Loaded environment variable {key} from {env_file}")
        except Exception as e:
            logger.error(f"Failed to load environment variables from {env_file}: {e}")

    def log_response(self, response):
        """Logs detailed information about the response if debug mode is enabled."""
        if self.debug:
            logger.debug(f"Status Code: {response.status_code}")
            logger.debug(f"Response Body: {response.text}")

    def get_public_ip(self) -> str:
        """Fetches the current public IP from an external API."""
        try:
            response = requests.get(self.public_ip_api)
            self.log_response(response)
            response.raise_for_status()
            ip = response.text.strip()
            logger.info(f"Fetched public IP: {ip}")
            return ip
        except requests.RequestException as e:
            logger.error(f"Error getting public IP: {e}")
            return None

    def delete_old_entry(self, item_id: str):
        """Deletes the old entry from the Cloudflare list using the item ID."""
        try:
            delete_payload = {
                "items": [{"id": item_id}]
            }
            response = requests.delete(self.cloudflare_list_api_url, headers=self.headers, json=delete_payload)
            self.log_response(response)
            response.raise_for_status()
            logger.info(f"Deleted item with ID: {item_id}")
        except requests.RequestException as e:
            logger.error(f"Error deleting item from Cloudflare list: {e}")

    def add_new_entry(self, ip: str):
        """Adds the new IP entry to the Cloudflare list."""
        try:
            add_payload = [{
                "ip": ip,
                "comment": self.comment
            }]
            response = requests.post(self.cloudflare_list_api_url, headers=self.headers, json=add_payload)
            self.log_response(response)
            response.raise_for_status()
            logger.info(f"Added new entry with IP: {ip}")
        except requests.RequestException as e:
            logger.error(f"Error adding new entry to Cloudflare list: {e}")

    def update_cloudflare_list(self, ip: str) -> None:
        """Updates the Cloudflare list with the new IP, replacing the old one if necessary."""
        try:
            # Get the current list entries from Cloudflare
            response = requests.get(self.cloudflare_list_api_url, headers=self.headers)
            self.log_response(response)
            response.raise_for_status()
            items = response.json().get('result', [])
            logger.info("Fetched current list from Cloudflare.")

            # Check if the public IP is already in the list
            for item in items:
                if item['content'] == ip:
                    logger.info(f"Public IP {ip} is already in the list, no update necessary.")
                    return

            # If the IP is not found in the list, proceed with updating
            logger.info(f"Public IP {ip} not found in the list. Proceeding with update.")

            # Find the entry to update (based on comment)
            for item in items:
                if item['comment'] == self.comment:
                    item_id = item['id']
                    # Delete the old entry using the item ID
                    self.delete_old_entry(item_id)
                    break

            # Add the new entry with the updated IP
            self.add_new_entry(ip)
        except requests.RequestException as e:
            logger.error(f"Error updating Cloudflare list: {e}")

    def run(self):
        """Main method to fetch IP and update Cloudflare."""
        current_ip = self.get_public_ip()
        if current_ip:
            logger.info(f"Current IP: {current_ip}, updating Cloudflare...")
            self.update_cloudflare_list(current_ip)
        else:
            logger.error("Failed to retrieve the public IP.")


if __name__ == "__main__":
    updater = CloudflareUpdater()
    updater.run()
