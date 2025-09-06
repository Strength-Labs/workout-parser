### Strength Coaching Markup Language**

The json2markup.py script converts workout data from the Turnkey Coach API's JSON format into a custom, human-readable plain text format. The markup is designed to be clear and structured, making it easy to read and understand the workout details, including comments and accomplished sets.

The workout_parser.py script converts text files in this markup language back into JSON suitable for the Turnkey Coach app. The workout_uploader.py script will upload the workouts to the app. 

### **Key Formatting Rules**

* **Workout Date**: Each workout begins with a Workout Date: line, followed by the date in YYYY-MM-DD format.  
  * **Example**: Workout Date: 2025-08-18  
* **Exercises**: The name of each exercise is on its own, un-indented line. It must be a valid exercise name from the exerciselist.json file.  
  * **Example**: Squat  
* **Assigned Sets**: The prescribed number of sets, reps, and weight are represented on a single, unindented line.  
  * **Examples**:  
    * 3x5 @ 405 (weight-based)  
    * 1x1 @ RPE 10 (RPE-based)  
    * 1xAMRAP @ 135 (AMRAP)  
    * 2x8 @ light (custom note)  
    * 2.5 miles @ 00:20:00 (distance-based)  
* **Accomplished Sets**: When a lifter records their actual performance, it is displayed on a new, unindented line enclosed in parentheses ().  
  * **Example**:  
    * Assigned: 3x5 @ 405  
    * Accomplished: (1x5 @ 405\)  
* **Comments and Notes**: These are all indented with a tab or spaces.  
  * **Comments to be Ignored**: These are conversational notes from a coach or client and are ignored by the workout\_parser.py script. They begin a name in brackets followed by a colon. Private coach's comments are indented with a \>. These comments are also ignored by the parser, but are for the coach or any AI agent to explain the reasoning for the program.   
    * **Examples**:  
      * \> He should go up 5% on squats next week.
      * \[Coachy McCoach\]: Great job on that lift\!  
      * \[Lifty McGee\]: I felt a pinch in my shoulder.  
  * **Notes to be Preserved**: Any other indented line that does not match the comment patterns above is treated as a custom note and will be preserved in the body field of the JSON output.  
    * **Example**: This should feel good\! Watch your knees\!  
* **Separators**: Each individual workout block is separated by a horizontal rule \---.

### **Sample:**

```
Workout Date: 2025-08-22

Squat  
3x5 @ 305  
  This should feel good\! Watch your knees\!  
  \>He should go up 5lbs, and squat every other workout.  
Press  
3x5 @ 115  
  \>These should go up 2.5lbs, every other workout.

Workout Date: 2025-05-25

Deadlift  
1x5 @ 405  
  \>Deadlifts are single sets of 5, increasing 5lbs each time, deadlifting every other workout for now.   
Bench Press  
3x5 @ 185  
  \>Increase by 2.5lbs, bench pressing every other workout.   
  \[Coachy McCoach\]: These workouts should give the pattern for the next three weeks, working out Monday, Wednesday, and Friday. 
  \[Client McClient\]: I like the pattern, but I'm starting to get worn out by deadlifts!
```

This format provides a complete and easily digestible view of a client's workout history, including the conversational feedback between the coach and the lifter.
