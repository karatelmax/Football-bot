import aiohttp
from typing import Optional, List, Dict, Any
from config import API_FOOTBALL_KEY, API_BASE_URL


class FootballAPI:
    def __init__(self):
        self.headers = {
            "x-apisports-key": API_FOOTBALL_KEY
        }
        self.session: Optional[aiohttp.ClientSession] = None

    async def start(self):
        self.session = aiohttp.ClientSession(headers=self.headers)

    async def close(self):
        if self.session:
            await self.session.close()

    async def _get(self, endpoint: str, params: dict = None) -> Dict[str, Any]:
        if not self.session:
            await self.start()
        url = f"{API_BASE_URL}/{endpoint}"
        async with self.session.get(url, params=params) as resp:
            data = await resp.json()
            if data.get("errors"):
                print(f"API Error: {data['errors']}")
            return data

    async def get_live_fixtures(self) -> List[Dict]:
        """Получить все текущие live матчи"""
        data = await self._get("fixtures", {"live": "all"})
        return data.get("response", [])

    async def get_fixture(self, fixture_id: int) -> Optional[Dict]:
        """Детали конкретного матча"""
        data = await self._get("fixtures", {"id": fixture_id})
        response = data.get("response", [])
        return response[0] if response else None

    async def get_fixture_statistics(self, fixture_id: int) -> List[Dict]:
        """Статистика матча (удары, владение и т.д.)"""
        data = await self._get("fixtures/statistics", {"fixture": fixture_id})
        return data.get("response", [])

    async def get_fixture_events(self, fixture_id: int) -> List[Dict]:
        """События матча (голы, карточки...)"""
        data = await self._get("fixtures/events", {"fixture": fixture_id})
        return data.get("response", [])

    async def get_h2h(self, team1_id: int, team2_id: int, last: int = 10) -> List[Dict]:
        """Head-to-head"""
        data = await self._get("fixtures/headtohead", {
            "h2h": f"{team1_id}-{team2_id}",
            "last": last
        })
        return data.get("response", [])

    async def get_team_statistics(self, team_id: int, league_id: int, season: int) -> Optional[Dict]:
        """Статистика команды в лиге"""
        data = await self._get("teams/statistics", {
            "team": team_id,
            "league": league_id,
            "season": season
        })
        return data.get("response")

    async def get_status(self) -> Dict:
        """Проверить лимиты API"""
        data = await self._get("status")
      
        return data.get("response", {})
