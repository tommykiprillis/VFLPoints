# VFLPoints

# Valorant Fantasy League Points Calculator

This project is a Python-based web scraper that fetches match data from [VLR.gg](https://www.vlr.gg) and calculates fantasy points for each player based on their performance.
The points are calculated via the scoring rules from [valorantfantasyleague.net](https://www.valorantfantasyleague.net/rules):

### Kills
- +1 for 10K in a map, +2 for 15K in a map, +3 for 20K in map etc.
- +1 for a 4K in a round
- +3 for a 5K+ in a round

### Map Wins
- +1 for any map win
- +2 for a 2-0 (a 2-0 would therefore receive 4 points)
- +1 for a map win by 5+ rounds, unless
- +2 for a map win by 10+ rounds
- -1 for a map loss by 10+ rounds

### Bonus
- +3, +2, +1 for top 3 highest scores in VLR rating for entire game, tiebreaker in ACS, if the same then both get the higher point score
- +1 for a VLR raying 1.5 or above in entire game
- +2 for VLR rating 1.75 or above in entire game
- +3 for VLR rating 2.0 or above in entire game

## Usage

### Running the Executable (.exe)
1. Double-click the `.exe` file.
2. Enter a match URL from VLR.gg when prompted.
3. The program will calculate and display fantasy league scores.

