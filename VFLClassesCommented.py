import requests
import re
from bs4 import BeautifulSoup

class VFLPointsCalculator:
    """
    A class to scrape and calculate fantasy league points for a Valorant match from VLR.gg.
    """
    def __init__(self, url):
        """
        Initialises the calculator with a given VLR.gg match URL.
        
        :param url: The URL of the match to scrape.
        """
        self.url = url
        self.players = []
        self.teams = []
        self.series_score = []
        self.map_game_ids = []
        self.main_soup = None
        self._initialise_main_page()

    def _initialise_main_page(self):
        """
        Fetches and parses the main match page, extracting team names, series scores, and game IDs.
        """
        main_html = self.get_html(self.url)
        self.main_soup = BeautifulSoup(main_html, 'html.parser')
        self._parse_main_page()

    def get_html(self, url):
        """
        Fetches HTML content from the given URL.
        
        :param url: The URL to fetch HTML from.
        :return: The raw HTML content as a string.
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    def _parse_main_page(self):
        """
        Parses the main page HTML to extract team names, series scores, and VLR rating.
        """
        team_divs = self.main_soup.find_all('div', 'match-header-link-name')[:2]
        self.teams = [re.sub(r'\s*\[.*?\]\s*', '', div.text.strip()) for div in team_divs]
        
        score_spans = []
        if spoiler_div := self.main_soup.find('div', 'js-spoiler'):
            score_spans = spoiler_div.find_all(
                'span', 
                class_=lambda x: x and any(c in x for c in ('match-header-vs-score-winner', 'match-header-vs-score-loser')))
        self.series_score = [int(s.text.strip()) for s in score_spans[:2]] if len(score_spans) >=2 else [0, 0]
        
        stats_container = self.main_soup.find('div', 'vm-stats-container')
        self.map_game_ids = []
        if stats_container:
            self.map_game_ids = [div['data-game-id'] for div in stats_container.select('div.vm-stats-game[data-game-id]') if div['data-game-id'] != 'all']
        
        if stats_container and (overall_container := stats_container.find('div', 'vm-stats-game mod-active', {'data-game-id': 'all'})):
            first_abbrev = None
            for table in overall_container.find_all('table', 'wf-table-inset mod-overview'):
                for row in table.find_all('tr')[1:]:
                    if team_div := row.find('div', 'ge-text-light'):
                        first_abbrev = team_div.text.strip().split()[0]
                        break
                if first_abbrev: break
            
            for table in overall_container.find_all('table', 'wf-table-inset mod-overview'):
                for row in table.find_all('tr')[1:]:
                    cells = row.find_all('td')
                    if not cells: continue
                    
                    player_name = cells[0].text.strip().split()[0]
                    team_div = row.find('div', 'ge-text-light')
                    team_abbrev = team_div.text.strip().split()[0] if team_div else None
                    team = self.teams[0] if team_abbrev == first_abbrev else self.teams[1]
                    
                    rating_span = row.find('span', 'side mod-side mod-both')
                    vlr_rating = float(rating_span.text.strip()) if rating_span else 0.0
                    acs = int(cells[3].text.strip().split()[0]) if cells[3].text.strip().split()[0] else 0
                    
                    self.players.append({
                        'name': player_name,
                        'team': team,
                        'vlr_rating': vlr_rating,
                        'acs': acs,
                        'kills': {},
                        '4K': 0,
                        '5K': 0,
                        'maps_won': 0,
                        'kills_points': 0,
                        'map_wins_points': 0,
                        'bonus_points': 0
                    })

    def parse_performance(self, html):
        """
        Parses the player performance data from the match's performance page.
        
        :param html: The HTML content of the performance tab.
        """
        soup = BeautifulSoup(html, 'html.parser')
        if not (table := soup.find('table', class_='wf-table-inset mod-adv-stats')):
            return
            
        headers = [th.text.strip().lower() for th in table.find('tr').find_all('th')]
        idx_4k = headers.index('4k') if '4k' in headers else -1
        idx_5k = headers.index('5k') if '5k' in headers else -1
        
        for row in table.find_all('tr')[1:]:
            cells = row.find_all('td')
            if not cells: continue
            
            player_name = cells[0].text.strip().lstrip().split()[0]
            for player in self.players:
                if player['name'] == player_name:
                    if idx_4k != -1:
                        player['4K'] = int(cells[idx_4k].text.strip()) if cells[idx_4k].text.strip() else 0
                    if idx_5k != -1:
                        player['5K'] = int(cells[idx_5k].text.strip()) if cells[idx_5k].text.strip() else 0
                    break

    def parse_map_page(self, html, game_id):
        """
        Parses the specific map page data from the maps page.
        
        :param html: The HTML content of the map page.
        :param game_id: The game ID of the map.
        """
        soup = BeautifulSoup(html, 'html.parser')
        map_container = soup.find('div', class_='vm-stats-game', attrs={'data-game-id': game_id})
        if not map_container:
            print(f"Map container for game_id {game_id} not found!")
            return
            
        score_divs = map_container.find_all('div', class_='score')[:2]
        scores = [int(div.text.strip()) for div in score_divs] if len(score_divs) >= 2 else [0, 0]
        winning_team_idx = 0 if scores[0] > scores[1] else 1
        winning_team = self.teams[winning_team_idx]
        losing_score = min(scores)
        
        for table in map_container.find_all('table', class_='wf-table-inset mod-overview'):
            for row in table.find_all('tr')[1:]:
                cells = row.find_all('td')
                if len(cells) < 5: continue
                
                player_name = cells[0].text.strip().lstrip().split()[0]
                kills_span = cells[4].find('span', class_='side mod-side mod-both')
                kills = int(kills_span.text.strip()) if kills_span and kills_span.text.strip() else 0
                
                for player in self.players:
                    if player['name'] == player_name:
                        player['kills'][game_id] = kills
                        break
        
        round_bonus = {0:2, 1:2, 2:2, 3:2, 4:1, 5:1, 6:1, 7:1, 8:1}.get(losing_score, 0)
        for player in self.players:
            if player['team'] == winning_team:
                player['map_wins_points'] += 1 + round_bonus
                player['maps_won'] += 1
            else:
                if losing_score <= 3:
                    player['map_wins_points'] -= 1

    def calculate_fantasy_scores(self):
        """
        Calculates fantasy points based on player performance, match stats, and bonuses.
        
        :return: A sorted list of players with their fantasy points.
        """
        # Process performance stats
        performance_html = self.get_html(f"{self.url}?game=all&tab=performance")
        self.parse_performance(performance_html)
        
        # Process map pages
        for game_id in self.map_game_ids:
            map_html = self.get_html(f"{self.url}?game={game_id}&tab=overview")
            self.parse_map_page(map_html, game_id)
        
        # Calculate kill points
        for player in self.players:
            # Kill milestones
            kill_points = sum(
                ((kills - 10) // 5 + 1 if kills >= 10 else 0
                for kills in player['kills'].values()
            ))
            # 4K/5K bonuses
            kill_points += player['4K'] * 1 + player['5K'] * 3
            player['kills_points'] = kill_points
        
        # Series win bonus
        winning_team = None
        for i in (0, 1):
            if self.series_score[i] == 2 and self.series_score[1 - i] == 0:
                winning_team = self.teams[i]
                break
        if winning_team:
            for player in self.players:
                 if player['team'] == winning_team:
                     player['map_wins_points'] += 2
        
        # Rating bonuses
        for player in self.players:
            if player['vlr_rating'] >= 2.0:
                player['bonus_points'] += 3
            elif player['vlr_rating'] >= 1.75:
                player['bonus_points'] += 2
            elif player['vlr_rating'] >= 1.5:
                player['bonus_points'] += 1
        
        # Top 3 bonuses
        sorted_players = sorted(self.players, key=lambda x: (-x['vlr_rating'], -x['acs']))
        for i, player in enumerate(sorted_players[:3]):
            player['bonus_points'] += (3 - i)
        
        # Prepare results
        result = []
        for player in self.players:
            total = player['kills_points'] + player['map_wins_points'] + player['bonus_points']
            result.append({
                'Player': player['name'],
                'Team': player['team'],
                'Kills': player['kills_points'],
                'Map Wins': player['map_wins_points'],
                'Bonus': player['bonus_points'],
                'Total': total
            })
        
        return sorted(result, key=lambda x: (-x['Total'], x['Player']))

if __name__ == "__main__":
    while True:
        url = input("\nEnter the VLR.gg match URL or press Enter to exit: ").strip()
        if not url:
            print("Exiting...")
            break
        try:
            calculator = VFLPointsCalculator(url)
            scores = calculator.calculate_fantasy_scores()
            print("\nValorant Fantasy League Scores: Total (Kills, Map Wins, Bonus)")
            for entry in scores:
                print(f"{entry['Player']} ({entry['Team']}): {entry['Total']} points ({entry['Kills']}, {entry['Map Wins']}, {entry['Bonus']})")
        except Exception as e:
            print(f"\nError processing URL: {e}")