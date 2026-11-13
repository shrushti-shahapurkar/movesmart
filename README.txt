MoveSmart - Four Additional Games
=================================

This pack is designed to be added to your EXISTING MoveSmart project.
It does not replace your app.py, database.db, login/register pages, or
existing three games.

1. Copy the four HTML files from templates/ into your project's templates/.
2. Copy the four JS files from static/js/ into your project's static/js/.
3. Copy the four route functions in app_routes_addition.py into app.py,
   near your existing /game/target-tap, /game/catch-object, and /game/sequence routes.
4. Confirm each HTML file links to its corresponding JS file.
5. Add links to these routes on your existing home/game-selection page.
6. Run: python app.py

The games submit results to your existing POST /save_game_result endpoint.
They use the same field names that your existing route expects:
game_name, score, accuracy, reaction_time, completion_time, errors,
objects_caught, objects_missed, path_deviation.

Important:
- These are educational game activities, not diagnostic tests.
- The existing CSV file must already have the header row created by init_database().
- Your existing app.py currently stores passwords as plain text. For any real use,
  change to password hashing before storing real accounts.
