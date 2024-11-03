import requests
import json
import os
from urllib.parse import parse_qs, unquote
from colorama import *
from datetime import datetime
import time
import pytz

wib = pytz.timezone('Asia/Jakarta')

class CartaWallet:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.headers = {
            'Accept': 'application/graphql-response+json, application/graphql+json, application/json, text/event-stream, multipart/mixed',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Host': 'api-crewdrop.cartawallet.com',
            'Origin': 'https://crewdrop.cartawallet.com',
            'Pragma': 'no-cache',
            'Referer': 'https://crewdrop.cartawallet.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0'
        }

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}Auto Claim {Fore.BLUE + Style.BRIGHT}Carta Wallet - BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    def extract_user_data(self, query: str) -> dict:
        parsed_query = parse_qs(query)
        user_data = parsed_query.get('user', [None])[0]

        if user_data:
            user_json = json.loads(unquote(user_data))
            return {
                "first_name": user_json.get("first_name", "Unknown"),
                "user_id": user_json.get("id")
            }
        return {"first_name": "Unknown", "user_id": None}

    def load_tokens(self):
        try:
            if not os.path.exists('tokens.json'):
                return {"accounts": []}

            with open('tokens.json', 'r') as file:
                data = json.load(file)
                if "accounts" not in data:
                    return {"accounts": []}
                return data
        except json.JSONDecodeError:
            return {"accounts": []}

    def save_tokens(self, tokens):
        with open('tokens.json', 'w') as file:
            json.dump(tokens, file, indent=4)

    def generate_tokens(self, queries: list):
        tokens_data = self.load_tokens()
        accounts = tokens_data["accounts"]

        for idx, query in enumerate(queries):
            account_name = self.extract_user_data(query)["first_name"]

            existing_account = next((acc for acc in accounts if acc["first_name"] == account_name), None)

            if not existing_account:
                print(
                    f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT}[ Account{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} {account_name} {Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT}Token Is None{Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT} ] [{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} Generating Token... {Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT}]{Style.RESET_ALL}",
                    end="\r", flush=True
                )
                time.sleep(1)

                token = self.user_auth(query)
                if token:
                    self.log(
                        f"{Fore.MAGENTA + Style.BRIGHT}[ Account{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} {account_name} {Style.RESET_ALL}"
                        f"{Fore.MAGENTA + Style.BRIGHT}] [{Style.RESET_ALL}"
                        f"{Fore.GREEN + Style.BRIGHT} Successfully Generated Token {Style.RESET_ALL}"
                        f"{Fore.MAGENTA + Style.BRIGHT}]{Style.RESET_ALL}                           "
                    )
                    accounts.insert(idx, {"first_name": account_name, "token": token})
                else:
                    self.log(
                        f"{Fore.MAGENTA + Style.BRIGHT}[ Account{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} {account_name} {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}Query Is Expired{Style.RESET_ALL}"
                        f"{Fore.MAGENTA + Style.BRIGHT} ] [{Style.RESET_ALL}"
                        f"{Fore.RED + Style.BRIGHT} Failed to Generate Token {Style.RESET_ALL}"
                        f"{Fore.MAGENTA + Style.BRIGHT}]{Style.RESET_ALL}                           "
                    )

                time.sleep(1)
                self.log(f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}" * 75)

        self.save_tokens({"accounts": accounts})

    def load_queries(self):
        with open('query.txt', 'r') as file:
            return [line.strip() for line in file if line.strip()]

    def user_auth(self, query: str, retries=5):
        url = 'https://api-crewdrop.cartawallet.com/v1/graphql'
        data = json.dumps({
            "operationName": "authenticate",
            "query": """mutation authenticate($initDataRaw: String!) {
                authenticate(initDataRaw: $initDataRaw) {
                    accessToken
                    __typename
                }
            }""",
            "variables": {
                "initDataRaw": query
            }
        })
        self.headers.update({
            'Content-Type': 'application/json'
        })

        for attempt in range(retries):
            try:
                response = self.session.post(url, headers=self.headers, data=data)
                if response.status_code == 200:
                    result = response.json()
                    if result:
                        return result['data']['authenticate']['accessToken']
                    else:
                        return None
                else:
                    return None
            except (requests.RequestException, ValueError) as e:
                if attempt < retries - 1:
                    print(
                        f"{Fore.RED+Style.BRIGHT}HTTP ERROR{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} Retrying... {Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT}[{attempt+1}/{retries}]{Style.RESET_ALL}",
                        end="\r",
                        flush=True
                    )
                    time.sleep(2)
                else:
                    return None
        
    def user_data(self, token: str, user_id: str, retries=5):
        url = 'https://api-crewdrop.cartawallet.com/v1/graphql'
        data = json.dumps({
            "operationName": "getMyData",
            "query": """query getMyData($userId: bigint = "") {
                user: userByPk(id: $userId) {
                    ...User
                    __typename
                }
            }
            fragment User on User {
                id
                createdAt
                balance
                isAllowPm
                lastClaimReferralAt
                referralCode
                referredByCode
                turn
                updatedAt
                __typename
            }""",
            "variables": {
                "userId": user_id
            }
        })
        self.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })

        for attempt in range(retries):
            try:
                response = self.session.post(url, headers=self.headers, data=data)
                if response.status_code == 200:
                    result = response.json()
                    if result:
                        return result['data']['user']
                    else:
                        return None
                else:
                    return None
            except (requests.RequestException, ValueError) as e:
                if attempt < retries - 1:
                    print(
                        f"{Fore.RED+Style.BRIGHT}HTTP ERROR{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} Retrying... {Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT}[{attempt+1}/{retries}]{Style.RESET_ALL}",
                        end="\r",
                        flush=True
                    )
                    time.sleep(2)
                else:
                    return None
                
    def tasks(self, token: str, retries=5):
        url = 'https://api-crewdrop.cartawallet.com/v1/graphql'
        data = json.dumps({
            "operationName": "getTasks",
            "query": """query getTasks {
                tasks: task(orderBy: {updatedAt: DESC}) {
                    ...Task
                    __typename
                }
            }
            fragment Task on Task {
                id
                frequency
                action
                createdAt
                status
                name
                point
                turn
                updatedAt
                value
                pendingSeconds
                __typename
            }""",
            "variables": {}
        })
        self.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })

        for attempt in range(retries):
            try:
                response = self.session.post(url, headers=self.headers, data=data)
                if response.status_code == 200:
                    result = response.json()
                    if result:
                        return result['data']['tasks']
                    else:
                        return None
                else:
                    return None
            except (requests.RequestException, ValueError) as e:
                if attempt < retries - 1:
                    print(
                        f"{Fore.RED+Style.BRIGHT}HTTP ERROR{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} Retrying... {Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT}[{attempt+1}/{retries}]{Style.RESET_ALL}",
                        end="\r",
                        flush=True
                    )
                    time.sleep(2)
                else:
                    return None
                
    def start_tasks(self, token: str, task_id: str, retries=5):
        url = 'https://api-crewdrop.cartawallet.com/v1/graphql'
        data = json.dumps({
            "operationName": "pushTaskAct",
            "query": """mutation pushTaskAct($act: String = "", $taskId: uuid = "") {
                pushTaskAct(act: $act, taskId: $taskId)
            }""",
            "variables": {
                "act": "start",
                "taskId": task_id
            }
        })
        self.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })

        for attempt in range(retries):
            try:
                response = self.session.post(url, headers=self.headers, data=data)
                if response.status_code == 200:
                    result = response.json()
                    if result:
                        return result['data']['pushTaskAct']
                    else:
                        return None
                else:
                    return None
            except (requests.RequestException, ValueError) as e:
                if attempt < retries - 1:
                    print(
                        f"{Fore.RED+Style.BRIGHT}HTTP ERROR{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} Retrying... {Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT}[{attempt+1}/{retries}]{Style.RESET_ALL}",
                        end="\r",
                        flush=True
                    )
                    time.sleep(2)
                else:
                    return None
                
    def claim_tasks(self, token: str, task_id: str, retries=5):
        url = 'https://api-crewdrop.cartawallet.com/v1/graphql'
        data = json.dumps({
            "operationName": "pushTaskAct",
            "query": """mutation pushTaskAct($act: String = "", $taskId: uuid = "") {
                pushTaskAct(act: $act, taskId: $taskId)
            }""",
            "variables": {
                "act": "claim",
                "taskId": task_id
            }
        })
        self.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })

        for attempt in range(retries):
            try:
                response = self.session.post(url, headers=self.headers, data=data)
                if response.status_code == 200:
                    result = response.json()
                    if result:
                        return result['data']['pushTaskAct']
                    else:
                        return None
                else:
                    return None
            except (requests.RequestException, ValueError) as e:
                if attempt < retries - 1:
                    print(
                        f"{Fore.RED+Style.BRIGHT}HTTP ERROR{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} Retrying... {Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT}[{attempt+1}/{retries}]{Style.RESET_ALL}",
                        end="\r",
                        flush=True
                    )
                    time.sleep(2)
                else:
                    return None
        
    def process_query(self, query: str):
        user_data = self.extract_user_data(query)
        account_name = user_data["first_name"]
        user_id = user_data["user_id"]

        tokens_data = self.load_tokens()
        accounts = tokens_data.get("accounts", [])

        exist_account = next((acc for acc in accounts if acc["first_name"] == account_name), None)
        if not exist_account:
            self.log(
                f"{Fore.MAGENTA + Style.BRIGHT}[ Account{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {account_name} {Style.RESET_ALL}"
                f"{Fore.RED + Style.BRIGHT}Token Not Found in tokens.json{Style.RESET_ALL}"
                f"{Fore.MAGENTA + Style.BRIGHT} ]{Style.RESET_ALL}"
            )
            return

        if exist_account and "token" in exist_account:
            token = exist_account["token"]
            
            user = self.user_data(token, user_id)
            if not user:
                self.log(
                    f"{Fore.MAGENTA+Style.BRIGHT}[ Account{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {account_name} {Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT}Token Is Expired{Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}] {Style.RESET_ALL}"
                )

            if user:
                self.log(
                    f"{Fore.MAGENTA+Style.BRIGHT}[ Account{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {account_name} {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}] [ Balance{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {user['balance']} $CREW {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}]{Style.RESET_ALL}"
                )
                time.sleep(1)

                tasks = self.tasks(token)
                if tasks:
                    for task in tasks:
                        task_id = task['id']
                        status = task['status']
                        delay = task['pendingSeconds']

                        if task and status == 'start':
                            start = self.start_tasks(token, task_id)
                            if start:
                                self.log(
                                    f"{Fore.MAGENTA+Style.BRIGHT}[ Task{Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT} {task['name']} {Style.RESET_ALL}"
                                    f"{Fore.GREEN+Style.BRIGHT}Is Started{Style.RESET_ALL}"
                                    f"{Fore.MAGENTA+Style.BRIGHT} ] [ Wait For{Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT} {delay} Seconds to Claim Rewards {Style.RESET_ALL}"
                                    f"{Fore.MAGENTA+Style.BRIGHT}]{Style.RESET_ALL}"
                                )
                                time.sleep(delay+1)

                                claim = self.claim_tasks(token, task_id)
                                if claim:
                                    self.log(
                                        f"{Fore.MAGENTA+Style.BRIGHT}[ Task{Style.RESET_ALL}"
                                        f"{Fore.WHITE+Style.BRIGHT} {task['name']} {Style.RESET_ALL}"
                                        f"{Fore.GREEN+Style.BRIGHT}Is Claimed{Style.RESET_ALL}"
                                        f"{Fore.MAGENTA+Style.BRIGHT} ] [ Reward{Style.RESET_ALL}"
                                        f"{Fore.WHITE+Style.BRIGHT} {task['point']} $CREW {Style.RESET_ALL}"
                                        f"{Fore.MAGENTA+Style.BRIGHT} {task['point']} $CREW {Style.RESET_ALL}"
                                        f"{Fore.WHITE+Style.BRIGHT} {task['turn']} Ticket {Style.RESET_ALL}"
                                        f"{Fore.MAGENTA+Style.BRIGHT}]{Style.RESET_ALL}"
                                    )
                                else:
                                    self.log(
                                        f"{Fore.MAGENTA+Style.BRIGHT}[ Task{Style.RESET_ALL}"
                                        f"{Fore.WHITE+Style.BRIGHT} {task['name']} {Style.RESET_ALL}"
                                        f"{Fore.RED+Style.BRIGHT}Isn't Claimed{Style.RESET_ALL}"
                                        f"{Fore.MAGENTA+Style.BRIGHT} ]{Style.RESET_ALL}"
                                    )
                                time.sleep(1)
                            else:
                                self.log(
                                    f"{Fore.MAGENTA+Style.BRIGHT}[ Task{Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT} {task['name']} {Style.RESET_ALL}"
                                    f"{Fore.RED+Style.BRIGHT}Isn't Started{Style.RESET_ALL}"
                                    f"{Fore.MAGENTA+Style.BRIGHT} ]{Style.RESET_ALL}"
                                )
                            time.sleep(1)

                        elif task and status == 'can_claim':
                            claim = self.claim_tasks(token, task_id)
                            if claim:
                                self.log(
                                    f"{Fore.MAGENTA+Style.BRIGHT}[ Task{Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT} {task['name']} {Style.RESET_ALL}"
                                    f"{Fore.GREEN+Style.BRIGHT}Is Claimed{Style.RESET_ALL}"
                                    f"{Fore.MAGENTA+Style.BRIGHT} ] [ Reward{Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT} {task['point']} $CREW {Style.RESET_ALL}"
                                    f"{Fore.MAGENTA+Style.BRIGHT} {task['point']} $CREW {Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT} {task['turn']} Ticket {Style.RESET_ALL}"
                                    f"{Fore.MAGENTA+Style.BRIGHT}]{Style.RESET_ALL}"
                                )
                            else:
                                self.log(
                                    f"{Fore.MAGENTA+Style.BRIGHT}[ Task{Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT} {task['name']} {Style.RESET_ALL}"
                                    f"{Fore.RED+Style.BRIGHT}Isn't Claimed{Style.RESET_ALL}"
                                    f"{Fore.MAGENTA+Style.BRIGHT} ]{Style.RESET_ALL}"
                                )
                            time.sleep(1)

                        else:
                            self.log(
                                f"{Fore.MAGENTA+Style.BRIGHT}[ Task{Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT} {task['name']} {Style.RESET_ALL}"
                                f"{Fore.YELLOW+Style.BRIGHT}Is Already Started{Style.RESET_ALL}"
                                f"{Fore.MAGENTA+Style.BRIGHT} ]{Style.RESET_ALL}"
                            )
                else:
                    self.log(
                        f"{Fore.MAGENTA+Style.BRIGHT}[ Task{Style.RESET_ALL}"
                        f"{Fore.GREEN+Style.BRIGHT} Is Completed {Style.RESET_ALL}"
                        f"{Fore.MAGENTA+Style.BRIGHT}]{Style.RESET_ALL}"
                    )
                
    def main(self):
        self.clear_terminal()
        try:
            queries = self.load_queries()
            self.generate_tokens(queries)

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(queries)}{Style.RESET_ALL}"
                )
                self.log(f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}"*75)

                for query in queries:
                    if query:
                        self.process_query(query)
                        self.log(f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}"*75)
                        time.sleep(3)

                seconds = 60
                while seconds > 0:
                    formatted_time = self.format_seconds(seconds)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}",
                        end="\r"
                    )
                    time.sleep(1)
                    seconds -= 1

        except KeyboardInterrupt:
            self.log(f"{Fore.RED + Style.BRIGHT}[ EXIT ] Carta Wallet - BOT{Style.RESET_ALL}")
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}An error occurred: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    bot = CartaWallet()
    bot.main()