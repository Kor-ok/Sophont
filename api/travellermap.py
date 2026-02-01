"""TravellerMap API client.

Provides both synchronous and asynchronous access to the TravellerMap.com API.

Usage (sync):
    api = TravellerMapAPI()
    data = api.fetch_world_data(0, 0)
    results = api.search("Regina")

Usage (async):
    async with TravellerMapAPI() as api:
        data = await api.fetch_world_data_async(0, 0)
        results = await api.search_async("Regina")
"""

# # Synchronous (simple, one-off calls)
# api = TravellerMapAPI()
# results = api.search("Regina")
# world = api.fetch_world_data(0, 0)

# # Asynchronous (efficient for multiple calls)
# async with TravellerMapAPI() as api:
#     results = await api.search_async("Regina")
#     world = await api.fetch_world_data_async(0, 0, milieu="M1105")

# # Coordinate conversion (pure utility, no network)
# x, y = TravellerMapAPI.convert_to_world_coordinates(sector_x=-4, sector_y=0, hex_x=19, hex_y=10)


from __future__ import annotations

import asyncio
from typing import Any

import httpx

BASE_URL = "https://travellermap.com/api"


class TravellerMapAPI:
    """Client for the TravellerMap.com API.

    Can be used as a context manager for async operations to ensure proper
    client lifecycle management, or instantiated directly for sync calls.
    """

    __slots__ = ("_async_client", "_timeout")

    def __init__(self, timeout: float = 30.0) -> None:
        """Initialise the API client.

        Args:
            timeout: Request timeout in seconds (default 30).
        """
        self._timeout = timeout
        self._async_client: httpx.AsyncClient | None = None

    # -------------------------------------------------------------------------
    # Context manager support (for async usage)
    # -------------------------------------------------------------------------

    async def __aenter__(self) -> TravellerMapAPI:
        """Enter async context, creating a reusable async client."""
        self._async_client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=self._timeout,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        """Exit async context, closing the async client."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None

    # -------------------------------------------------------------------------
    # Coordinate conversion (pure utility, no I/O)
    # -------------------------------------------------------------------------

    @staticmethod
    def convert_to_world_coordinates(
        sector_x: int,
        sector_y: int,
        hex_x: int,
        hex_y: int,
    ) -> tuple[int, int]:
        """Convert sector and hex coordinates to world-space X,Y coordinates.

        Args:
            sector_x: Sector X coordinate.
            sector_y: Sector Y coordinate.
            hex_x: Hex X coordinate within the sector (1-32).
            hex_y: Hex Y coordinate within the sector (1-40).

        Returns:
            Tuple of (world_x, world_y) coordinates.
        """
        SECTOR_WIDTH = 32
        SECTOR_HEIGHT = 40
        REFERENCE_SECTOR_X = 0
        REFERENCE_SECTOR_Y = 0
        REFERENCE_HEX_X = 1
        REFERENCE_HEX_Y = 40

        x = (sector_x - REFERENCE_SECTOR_X) * SECTOR_WIDTH + (hex_x - REFERENCE_HEX_X)
        y = (sector_y - REFERENCE_SECTOR_Y) * SECTOR_HEIGHT + (hex_y - REFERENCE_HEX_Y)
        return x, y

    # -------------------------------------------------------------------------
    # Async API methods
    # -------------------------------------------------------------------------

    async def _get_async_client(self) -> httpx.AsyncClient:
        """Return the async client, creating one if needed."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=BASE_URL,
                timeout=self._timeout,
            )
        return self._async_client

    async def fetch_world_data_async(
        self,
        world_x: int,
        world_y: int,
        milieu: str | None = None,
    ) -> dict[str, Any]:
        """Fetch world/credits data for given coordinates (async).

        Args:
            world_x: World X coordinate.
            world_y: World Y coordinate.
            milieu: Optional milieu identifier (e.g., "M1105").

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            httpx.HTTPStatusError: If the request fails.
            ValueError: If the response is not valid JSON.
        """
        client = await self._get_async_client()
        params: dict[str, str] = {"x": str(world_x), "y": str(world_y)}
        if milieu:
            params["milieu"] = milieu

        response = await client.get("/credits", params=params)
        response.raise_for_status()

        try:
            return response.json()
        except ValueError as e:
            raise ValueError("Failed to parse JSON response") from e

    async def search_async(self, query: str) -> dict[str, Any]:
        """Search TravellerMap for worlds, sectors, etc. (async).

        Args:
            query: Search term (e.g., "Regina", "Spinward Marches").

        Returns:
            Parsed JSON response as a dictionary containing search results.

        Raises:
            httpx.HTTPStatusError: If the request fails.
            ValueError: If the response is not valid JSON.
        """
        client = await self._get_async_client()
        response = await client.get("/search", params={"q": query})
        response.raise_for_status()

        if not response.text:
            return {"Results": {"Items": []}}

        try:
            return response.json()
        except ValueError as e:
            raise ValueError("Failed to parse JSON response") from e

    async def fetch_sector_data_async(
        self,
        sector: str,
        milieu: str | None = None,
    ) -> dict[str, Any]:
        """Fetch sector metadata (async).

        Args:
            sector: Sector name or coordinates (e.g., "Spinward Marches" or "spin").
            milieu: Optional milieu identifier.

        Returns:
            Parsed JSON response as a dictionary.
        """
        client = await self._get_async_client()
        params: dict[str, str] = {"sector": sector}
        if milieu:
            params["milieu"] = milieu

        response = await client.get("/sec", params=params, headers={"Accept": "application/json"})
        response.raise_for_status()

        try:
            return response.json()
        except ValueError as e:
            raise ValueError("Failed to parse JSON response") from e

    async def close_async(self) -> None:
        """Explicitly close the async client if not using context manager."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None

    # -------------------------------------------------------------------------
    # Synchronous wrappers (convenience for non-async contexts)
    # -------------------------------------------------------------------------

    def fetch_world_data(
        self,
        world_x: int,
        world_y: int,
        milieu: str | None = None,
    ) -> dict[str, Any]:
        """Fetch world/credits data for given coordinates (sync).

        This is a convenience wrapper that runs the async method in a new
        event loop. For multiple calls, prefer using the async interface.

        Args:
            world_x: World X coordinate.
            world_y: World Y coordinate.
            milieu: Optional milieu identifier.

        Returns:
            Parsed JSON response as a dictionary.
        """
        return self._run_sync(self.fetch_world_data_async(world_x, world_y, milieu))

    def search(self, query: str) -> dict[str, Any]:
        """Search TravellerMap for worlds, sectors, etc. (sync).

        Args:
            query: Search term.

        Returns:
            Parsed JSON response as a dictionary.
        """
        return self._run_sync(self.search_async(query))

    def fetch_sector_data(
        self,
        sector: str,
        milieu: str | None = None,
    ) -> dict[str, Any]:
        """Fetch sector metadata (sync).

        Args:
            sector: Sector name or coordinates.
            milieu: Optional milieu identifier.

        Returns:
            Parsed JSON response as a dictionary.
        """
        return self._run_sync(self.fetch_sector_data_async(sector, milieu))

    def _run_sync(self, coro) -> Any:  # noqa: ANN001
        """Run an async coroutine synchronously.

        Handles the case where we're already in an async context by using
        a new event loop in a thread.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is None:
            # No event loop running; safe to use asyncio.run()
            return asyncio.run(coro)
        else:
            # Already in an async context; run in a thread to avoid blocking
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
