### json2markup.py Markup Language

The `json2markup.py` script converts workout data from the Turnkey Coach API's JSON format into a custom, human-readable plain text format. The markup is designed to be clear and structured, making it easy to read and understand the workout details, including comments and accomplished sets.

***

### Key Formatting Rules

* **Workout Date**: Each workout begins with a `Workout Date:` line, followed by the date in `YYYY-MM-DD` format.
    * **Example**: `Workout Date: 2025-08-18`

* **Exercises**: The name of each exercise is on its own, un-indented line. It must be a valid exercise name from the `exerciselist.json` file.
    * **Example**: `Squat`

* **Assigned Sets**: The prescribed number of sets, reps, and weight are represented on a single, tab-indented line.
    * **Examples**:
        * `3x5 @ 405` (weight-based)
        * `1x1 @ RPE 10` (RPE-based)
        * `1xAMRAP @ 135` (AMRAP)
        * `2x8 @ light` (custom note)
        * `2.5 miles @ 00:20:00` (distance-based)

* **Accomplished Sets**: When a lifter records their actual performance, it is displayed on a new, tab-indented line enclosed in parentheses `()`.
    * **Example**:
        * Assigned: `3x5 @ 405`
        * Accomplished: `(1x5 @ 405)`

* **Comments**: Comments from the coach and client are clearly distinguished and indented with a tab.
    * **Coach Comments**: Displayed with the coach's full name in brackets.
        * **Example**: `[Coachy McCoach]: Great job on that lift!`
    * **Client Comments**: Displayed with the client's full name in brackets.
        * **Example**: `[Lifty McGee]: I felt a pinch in my shoulder.`

* **Separators**: Each individual workout block is separated by a horizontal rule `---`.

* **Coach Notes (Private)**: These are notes for the coach's eyes only and are ignored by the JSON converter. They are formatted with a > at the beginning of the line, following a tab. This is for the coach to describe the reasoning behind the programming, or for the LLM/AI to explain its reasoning when writing programming.

  * **Example**: > I'm increasing 5lbs from the last set. We'll continue this pattern for a few more weeks.


Sample:

```

Workout Date: 2025-08-22

Squat
3x5 @ 305
  >He should go up 5lbs, and squat every other workout.
Press
3x5 @ 115
  >These should go up 2.5lbs, every other workout.

Workout Date: 2025-05-25

Deadlift
1x5 @ 405
  >Deadlifts are single sets of 5, increasing 5lbs each time, deadlifting every other workout for now. 
Bench Press
3x5 @ 185
  >Increase by 2.5lbs, bench pressing every other workout. 
  >These workouts should give the pattern for the next three weeks, working out Monday, Wednesday, and Friday. 

```

This format provides a complete and easily digestible view of a client's workout history, including the conversational feedback between the coach and the lifter.
Workout Date: 2025-08-22

Squat
3x5 @ 305
  >He should go up 5lbs, and squat every other workout.
Press
3x5 @ 115
  >These should go up 2.5lbs, every other workout.

Workout Date: 2025-05-25

Deadlift
1x5 @ 405
  >Deadlifts are single sets of 5, increasing 5lbs each time, deadlifting every other workout for now. 
Bench Press
3x5 @ 185
  >Increase by 2.5lbs, bench pressing every other workout. 
  >These workouts should give the pattern for the next three weeks, working out Monday, Wednesday, and Friday. 
