# Team Jeremy

Here is our implementation for the CSE140 Pacman AI tournament

## Instructions to run

Inside the pacman repo, make sure pacai/student/myTeam.py is up to date.

Run using

```sh
python3 -m pacai.bin.capture --red pacai.core.baselineTeam --blue pacai.student.myTeam
```

test a custom team against another with
```sh
python3 -m pacai.bin.capture --red pacai.core.myTeam --blue pacai.student.<other_file>
```

Latest updates: 
defensive agent takes into account enemy invader distance to capsule

offensive agent takes into account distance to capsule, scared ghosts, and corners
