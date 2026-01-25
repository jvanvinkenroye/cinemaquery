"""Interactive mode for cinemaquery with fuzzy selection menus."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from simple_term_menu import TerminalMenu  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from .client import CineamoClient

console = Console()


# Menu choice constants
CHOICE_CINEMA = "cinema"
CHOICE_MOVIE = "movie"
CHOICE_BACK = "back"
CHOICE_QUIT = "quit"


def format_cinema_entry(cinema: dict[str, Any]) -> str:
    """Format a cinema dict as a menu entry string."""
    name = str(cinema.get("name", "Unknown"))
    city = str(cinema.get("city", ""))
    country = str(cinema.get("countryCode", ""))
    location = f"{city}, {country}" if city else country
    if location:
        return f"{name}  [{location}]"
    return name


def format_movie_entry(movie: dict[str, Any]) -> str:
    """Format a movie dict as a menu entry string."""
    title = str(movie.get("title", "Unknown"))
    runtime = movie.get("runtime")
    release = str(movie.get("releaseDate", ""))
    suffix_parts: list[str] = []
    if runtime:
        suffix_parts.append(f"{runtime} min")
    if release:
        suffix_parts.append(release[:10])  # Just the date part
    if suffix_parts:
        return f"{title}  [{', '.join(suffix_parts)}]"
    return title


def format_showtime_entry(showing: dict[str, Any]) -> str:
    """Format a showtime dict as a menu entry string."""
    start_dt = datetime.fromisoformat(showing["startDatetime"].replace("Z", "+00:00"))
    time_str = start_dt.strftime("%H:%M")
    name = showing.get("name", "Unknown")
    language = showing.get("language", "")
    is_ov = showing.get("isOriginalLanguage", False)
    lang_info = "OV" if is_ov else language
    return f"{time_str}  {name}  [{lang_info}]"


def load_cinemas_with_progress(
    client: CineamoClient,
    city: str | None = None,
    movie_id: int | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """Load cinemas with a progress spinner."""
    cinemas: list[dict[str, Any]] = []
    params: dict[str, Any] = {}
    if city:
        params["city"] = city
    if movie_id:
        params["movieId"] = movie_id

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(description="Loading cinemas...", total=None)
        for cinema in client.stream_all("/cinemas", per_page=50, **params):
            cinemas.append(cinema)
            if limit and len(cinemas) >= limit:
                break
    return cinemas


def load_movies_with_progress(
    client: CineamoClient,
    query: str | None = None,
    cinema_id: int | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """Load movies with a progress spinner."""
    movies: list[dict[str, Any]] = []
    params: dict[str, Any] = {}
    if query:
        params["query"] = query

    path = f"/cinemas/{cinema_id}/movies" if cinema_id else "/movies"

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(description="Loading movies...", total=None)
        for movie in client.stream_all(path, per_page=50, **params):
            movies.append(movie)
            if limit and len(movies) >= limit:
                break
    return movies


def load_showtimes_with_progress(
    client: CineamoClient,
    cinema_id: int,
    date: datetime,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Load showtimes for a specific cinema and date."""
    showtimes: list[dict[str, Any]] = []
    start_datetime = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_datetime = start_datetime + timedelta(days=1)

    params: dict[str, Any] = {
        "cinemaIds[]": cinema_id,
        "startDatetime": start_datetime.isoformat().replace("+00:00", "Z"),
        "endDatetime": end_datetime.isoformat().replace("+00:00", "Z"),
    }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(description="Loading showtimes...", total=None)
        for showing in client.stream_all("/showings", per_page=50, **params):
            showtimes.append(showing)
            if limit and len(showtimes) >= limit:
                break

    # Sort by start time
    showtimes.sort(key=lambda s: s.get("startDatetime", ""))
    return showtimes


def show_fuzzy_menu(
    title: str,
    entries: list[str],
    preview_command: str | None = None,
    multi_select: bool = False,
) -> int | list[int] | None:
    """Show a fuzzy search menu and return the selected index(es)."""
    if not entries:
        console.print("[yellow]No items found.[/yellow]")
        return None

    menu = TerminalMenu(
        entries,
        title=title,
        search_key=None,  # Search through all text
        show_search_hint=True,
        search_highlight_style=("fg_yellow", "bold"),
        multi_select=multi_select,
        show_multi_select_hint=multi_select,
    )
    result: int | list[int] | None = menu.show()
    return result


def show_main_menu() -> str | None:
    """Show the main menu and return the selected action."""
    entries = [
        "[c] Search for a cinema",
        "[m] Search for a movie",
        "[q] Exit",
    ]
    menu = TerminalMenu(
        entries,
        title="What would you like to do?",
        shortcut_key_highlight_style=("fg_yellow",),
    )
    result = menu.show()
    if result is None:
        return None
    if result == 0:
        return CHOICE_CINEMA
    if result == 1:
        return CHOICE_MOVIE
    return CHOICE_QUIT


def show_cinema_action_menu(cinema_name: str) -> str:
    """Show actions available for a selected cinema."""
    entries = [
        "[t] Show today's showtimes",
        "[s] Show showtimes for another date",
        "[m] Show movies at this cinema",
        "[d] Show cinema details",
        "[b] Back to main menu",
    ]
    actions = ["showtimes_today", "showtimes_date", "movies", "details", CHOICE_BACK]
    menu = TerminalMenu(
        entries,
        title=f'Actions for "{cinema_name}":',
        shortcut_key_highlight_style=("fg_yellow",),
    )
    result: int | None = menu.show()
    if result is None:
        return CHOICE_BACK
    return actions[result]


def show_movie_action_menu(movie_title: str) -> str:
    """Show actions available for a selected movie."""
    entries = [
        "[c] Show cinemas playing this movie",
        "[d] Show movie details",
        "[b] Back",
    ]
    actions = ["cinemas", "details", CHOICE_BACK]
    menu = TerminalMenu(
        entries,
        title=f'Actions for "{movie_title}":',
        shortcut_key_highlight_style=("fg_yellow",),
    )
    result: int | None = menu.show()
    if result is None:
        return CHOICE_BACK
    return actions[result]


def prompt_date() -> datetime | None:
    """Prompt user for a date selection."""
    today = datetime.now(timezone.utc)
    dates = [today + timedelta(days=i) for i in range(14)]
    entries = [d.strftime("%A, %Y-%m-%d") for d in dates]

    menu = TerminalMenu(
        entries,
        title="Select a date:",
    )
    result: int | None = menu.show()
    if result is None:
        return None
    return dates[result]


def prompt_city() -> str | None:
    """Prompt user for optional city filter."""
    console.print("[dim]Enter a city name to filter (or press Enter to skip):[/dim]")
    try:
        city = input("> ").strip()
        return city if city else None
    except (KeyboardInterrupt, EOFError):
        return None


def prompt_movie_query() -> str | None:
    """Prompt user for optional movie search query."""
    console.print(
        "[dim]Enter a movie title to search (or press Enter to list all):[/dim]"
    )
    try:
        query = input("> ").strip()
        return query if query else None
    except (KeyboardInterrupt, EOFError):
        return None


def display_cinema_details(client: CineamoClient, cinema_id: int) -> None:
    """Display details for a cinema."""
    data = client.get_json(f"/cinemas/{cinema_id}")
    table = Table(title=f"Cinema Details (ID: {cinema_id})", header_style="bold cyan")
    table.add_column("Field", style="magenta", no_wrap=True)
    table.add_column("Value")
    for key in ("id", "name", "city", "countryCode", "slug", "ticketSystem", "email"):
        table.add_row(key, str(data.get(key, "")))
    console.print(table)


def _format_runtime(minutes: int | None) -> str:
    """Format runtime in hours and minutes."""
    if not minutes:
        return ""
    hours, mins = divmod(minutes, 60)
    if hours:
        return f"{hours}h {mins}min ({minutes} min)"
    return f"{mins} min"


def _format_genres(genres: list[dict[str, Any]] | None) -> str:
    """Format genres list."""
    if not genres:
        return ""
    return ", ".join(g.get("name", "") for g in genres if g.get("name"))


def display_movie_details(client: CineamoClient, movie_id: int) -> None:
    """Display details for a movie."""
    data = client.get_json(f"/movies/{movie_id}")

    title = data.get("title", "Unknown")
    original_title = data.get("originalTitle", "")

    console.print()
    console.print(f"[bold cyan]{title}[/bold cyan]")
    if original_title and original_title != title:
        console.print(f"[dim]({original_title})[/dim]")
    console.print()

    # Main info table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="magenta", no_wrap=True)
    table.add_column("Value")

    table.add_row("Runtime", _format_runtime(data.get("runtime")))
    table.add_row("Release", str(data.get("releaseDate", ""))[:10])
    table.add_row("Genres", _format_genres(data.get("genres")))
    table.add_row("Language", str(data.get("originalLanguage", "")))
    table.add_row("IMDb", str(data.get("imdbId", "")))
    table.add_row("TMDB", str(data.get("tmdbId", "")))

    console.print(table)

    # Overview/Plot
    overview = data.get("overview")
    if overview:
        console.print()
        console.print("[bold]Overview:[/bold]")
        # Wrap text at ~80 chars
        console.print(f"[dim]{overview}[/dim]", width=80)


def display_showtimes_table(
    showtimes: list[dict[str, Any]], cinema_name: str, date: datetime
) -> None:
    """Display showtimes in a rich table."""
    date_str = date.strftime("%Y-%m-%d")
    table = Table(
        title=f'Showtimes for "{cinema_name}" on {date_str}',
        header_style="bold cyan",
        show_lines=False,
    )
    table.add_column("Time", style="green", no_wrap=True)
    table.add_column("Movie", style="bold")
    table.add_column("Language", style="yellow", no_wrap=True)
    table.add_column("Original", style="magenta", no_wrap=True)

    for showing in showtimes:
        start_dt = datetime.fromisoformat(
            showing["startDatetime"].replace("Z", "+00:00")
        )
        table.add_row(
            start_dt.strftime("%H:%M"),
            str(showing.get("name", "")),
            str(showing.get("language", "")),
            "OV" if showing.get("isOriginalLanguage") else "",
        )
    console.print(table)


def _wait_for_continue() -> None:
    """Wait for user to press Enter."""
    console.print()
    console.print("[dim]Press Enter to continue...[/dim]", end="")
    input()


def _handle_showtimes(
    client: CineamoClient, cinema_id: int, cinema_name: str, date: datetime
) -> None:
    """Handle showing showtimes for a specific date."""
    showtimes = load_showtimes_with_progress(client, cinema_id, date)
    if showtimes:
        display_showtimes_table(showtimes, cinema_name, date)
    else:
        date_str = date.strftime("%Y-%m-%d")
        console.print(f"[yellow]No showtimes found for {date_str}.[/yellow]")
    _wait_for_continue()


def _handle_cinema_movies(
    client: CineamoClient, cinema_id: int, cinema_name: str
) -> None:
    """Handle showing movies at a cinema with selection."""
    movies = load_movies_with_progress(client, cinema_id=cinema_id)
    if not movies:
        console.print("[yellow]No movies found at this cinema.[/yellow]")
        _wait_for_continue()
        return

    movie_entries = [format_movie_entry(m) for m in movies]
    console.print(f"[dim]Found {len(movies)} movies. Use fuzzy search to filter.[/dim]")
    movie_idx = show_fuzzy_menu(f'Movies at "{cinema_name}":', movie_entries)
    if movie_idx is not None:
        selected_movie = movies[movie_idx]  # type: ignore[index]
        movie_id = selected_movie["id"]
        movie_title = selected_movie.get("title", "Unknown")
        cineamo_id = selected_movie.get("cineamoId")

        # Show movie action menu
        while True:
            console.print()
            action = show_movie_action_menu(str(movie_title))
            if action == CHOICE_BACK or action is None:
                break
            if action == "details":
                display_movie_details(client, movie_id)
                _wait_for_continue()
            elif action == "cinemas":
                _handle_movie_cinemas(client, movie_id, str(movie_title), cineamo_id)


def _handle_movie_cinemas(
    client: CineamoClient, movie_id: int, movie_title: str, cineamo_id: str | None
) -> None:
    """Handle showing cinemas that play a specific movie."""
    # Ask for city filter (important because there can be 1000+ cinemas)
    city = prompt_city()
    cinemas = load_cinemas_with_progress(client, movie_id=movie_id, city=city)
    if not cinemas:
        console.print("[yellow]No cinemas found playing this movie.[/yellow]")
        _wait_for_continue()
        return

    cinema_entries = [format_cinema_entry(c) for c in cinemas]
    console.print(
        f"[dim]Found {len(cinemas)} cinemas. Use fuzzy search to filter.[/dim]"
    )
    cinema_idx = show_fuzzy_menu(f'Cinemas playing "{movie_title}":', cinema_entries)
    if cinema_idx is not None:
        selected_cinema = cinemas[cinema_idx]  # type: ignore[index]
        cinema_id = selected_cinema["id"]
        cinema_name = selected_cinema.get("name", "Unknown")

        # Show showtimes for this movie at this cinema
        console.print()
        console.print(f'[bold]Showtimes for "{movie_title}" at {cinema_name}:[/bold]')
        today = datetime.now(timezone.utc)
        showtimes = load_showtimes_with_progress(client, cinema_id, today)

        # Filter showtimes for this movie by cineamoMovieId
        if cineamo_id:
            movie_showtimes = [
                s for s in showtimes
                if s.get("cineamoMovieId") == cineamo_id
            ]
        else:
            # Fallback to name matching
            movie_showtimes = [
                s for s in showtimes
                if movie_title.lower() in str(s.get("name", "")).lower()
            ]

        if movie_showtimes:
            display_showtimes_table(movie_showtimes, cinema_name, today)
        else:
            console.print("[yellow]No showtimes found for today.[/yellow]")
        _wait_for_continue()


def _handle_cinema_action(
    client: CineamoClient, cinema_id: int, cinema_name: str, action: str
) -> None:
    """Handle a single cinema action."""
    if action == "details":
        display_cinema_details(client, cinema_id)
        _wait_for_continue()
    elif action == "showtimes_today":
        _handle_showtimes(client, cinema_id, cinema_name, datetime.now(timezone.utc))
    elif action == "showtimes_date":
        selected_date = prompt_date()
        if selected_date:
            _handle_showtimes(client, cinema_id, cinema_name, selected_date)
    elif action == "movies":
        _handle_cinema_movies(client, cinema_id, cinema_name)


def run_cinema_workflow(client: CineamoClient) -> bool:
    """Run the cinema selection and action workflow. Returns False to exit."""
    city = prompt_city()
    cinemas = load_cinemas_with_progress(client, city=city)
    if not cinemas:
        console.print("[yellow]No cinemas found.[/yellow]")
        return True

    entries = [format_cinema_entry(c) for c in cinemas]
    console.print(
        f"[dim]Found {len(cinemas)} cinemas. Use fuzzy search to filter.[/dim]"
    )

    selected_idx = show_fuzzy_menu("Select a cinema:", entries)
    if selected_idx is None:
        return True

    selected_cinema = cinemas[selected_idx]  # type: ignore[index]
    cinema_id = selected_cinema["id"]
    cinema_name = selected_cinema.get("name", "Unknown")

    while True:
        console.print()
        action = show_cinema_action_menu(cinema_name)
        if action == CHOICE_BACK or action is None:
            return True
        _handle_cinema_action(client, cinema_id, cinema_name, action)


def run_movie_workflow(client: CineamoClient) -> bool:
    """Run the movie selection and action workflow. Returns False to exit."""
    # Optional query
    query = prompt_movie_query()

    # Load and display movies
    movies = load_movies_with_progress(client, query=query)
    if not movies:
        console.print("[yellow]No movies found.[/yellow]")
        return True

    # Format entries for fuzzy menu
    entries = [format_movie_entry(m) for m in movies]
    console.print(f"[dim]Found {len(movies)} movies. Use fuzzy search to filter.[/dim]")

    # Movie selection
    selected_idx = show_fuzzy_menu("Select a movie:", entries)
    if selected_idx is None:
        return True

    selected_movie = movies[selected_idx]  # type: ignore[index]
    movie_id = selected_movie["id"]
    movie_title = selected_movie.get("title", "Unknown")
    cineamo_id = selected_movie.get("cineamoId")

    # Movie action loop
    while True:
        console.print()
        action = show_movie_action_menu(str(movie_title))

        if action == CHOICE_BACK or action is None:
            return True

        if action == "details":
            display_movie_details(client, movie_id)
            _wait_for_continue()

        elif action == "cinemas":
            _handle_movie_cinemas(client, movie_id, str(movie_title), cineamo_id)


def run_interactive(client: CineamoClient, start_type: str | None = None) -> None:
    """Main entry point for interactive mode."""
    console.print("[bold cyan]Cinemaquery Interactive Mode[/bold cyan]")
    hint = "Use arrow keys to navigate, type to filter, Enter to select, Esc to cancel"
    console.print(f"[dim]{hint}[/dim]")
    console.print()

    # If a specific type was requested, go directly to that workflow
    if start_type == "cinema":
        run_cinema_workflow(client)
        return
    if start_type == "movie":
        run_movie_workflow(client)
        return

    # Main menu loop
    while True:
        choice = show_main_menu()

        if choice is None or choice == CHOICE_QUIT:
            console.print("[dim]Goodbye![/dim]")
            break

        if choice == CHOICE_CINEMA:
            run_cinema_workflow(client)

        elif choice == CHOICE_MOVIE:
            run_movie_workflow(client)
