((problem SPS)
  (:domain SPS)
  (:objects
    human1 robot1 cart - agent
    location1a location1b location1c location2a location2b location2c - location
    part2  - part
    rhand1 lhand1 robothand1 part2_holder - holder
  )
  (:init
    (neighbor location0b location1b) (neighbor location1b location2b)
    (neighbor location1b location0b) (neighbor location2b location1b)
    (neighbor location0a location0b) (neighbor location1a location1b) (neighbor location2a location2b)
    (neighbor location0b location0a) (neighbor location1b location1a) (neighbor location2b location2a)
    (neighbor location0c location1c) (neighbor location1c location2c)
    (neighbor location1c location0c) (neighbor location2c location1c)
    (neighbor location0b location0c) (neighbor location1b location1c) (neighbor location2b location2c)
    (neighbor location0c location0b) (neighbor location1c location1b) (neighbor location2c location2b)
    (locate part2 location1a)
    (at human1 location1b)
    (at robot1 location2b)
    (at cart location1c)
    (free lhand1)
    (free robothand1)
    (free part2_holder)
    (occupied location1b)
    (occupied location2b)
    (belong human1 lhand1)
    (belong human1 rhand1)
    (belong robot1 robothand1)
    (belong cart part2_holder)
  )

  (:goal
    (and
    (at human1 location1b) (at robot1 location2b) (at cart location1c) (on part2 robothand1)
    )
  )
)