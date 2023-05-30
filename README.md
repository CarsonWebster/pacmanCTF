# Team Jeremy

Here is our implementation for the CSE140 Pacman AI tournament

## Instructions to run

Inside the pacman repo, make sure pacai/student/myTeam.py is up to date.

Run using

```sh
python3 -m pacai.bin.capture --red pacai.core.baselineTeam --blue pacai.student.myTeam
```

Latest pdates: 
Update check for if we Pacman eats a scared ghost:
  checking if distance to ghost == 0 didn't work, as ghost gets reset to start position when it's eaten
    currently checking if there is less scared ghosts in successor state than the current state, and ghost scared time > 1
      -time check should avoid awarding pacman simply because scared timer is now over
    
Updated Defensive agent:
  reward it for being close to the enemy regardless of whether or not the enemy is invading, should incentivize ghost
    to stay around the middle as opposed to randomly wandering around when there are no invaders.
