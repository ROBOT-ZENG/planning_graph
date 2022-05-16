((domain SPS)
  (:requirements :strips :typing :negative-preconditions :equality)
  (:types
    location
    agent
    holder
    part
  )
  
  (:predicates
    (neighbor ?l1 - location ?l2 - location)
    (at ?ag - agent ?l - location)
    (occupied ?l - location)
    (free ?h - holder)
    (locate ?p - part ?l - location)
    (on ?p - part ?h - holder)
    (belong ?ag - agent ?h - holder)
    (getnew ?p1 - part ?p2 - part ?p12 - part)
  )

  (:action pick
    :parameters (?ag - agent ?p - part ?l1 - location ?l2 - location ?h - holder)
    :precondition (and (at ?ag ?l1) (locate ?p ?l2) (neighbor ?l1 ?l2) (free ?h) (belong ?ag ?h))
    :effect (and (not (free ?h)) (on ?p ?h) (not (locate ?p ?l2)))
  )

  (:action pass
    :parameters (?ag1 - agent ?ag2 - agent ?l1 - location ?l2 - location ?p - part ?h1 - holder ?h2 - holder)
    :precondition (and (at ?ag1 ?l1) (at ?ag2 ?l2) (neighbor ?l1 ?l2) (belong ?ag1 ?h1) (on ?p ?h1) (belong ?ag2 ?h2) (free ?h2))
    :effect (and (not (on ?p ?h1)) (free ?h1) (on ?p ?h2) (not (free ?h2)))
  )

  (:action move
    :parameters (?ag - agent ?from - location ?to - location)
    :precondition (and (neighbor ?from ?to) (at ?ag ?from) (not (occupied ?to)))
    :effect (and (at ?ag ?to) (not (occupied ?from)) (occupied ?to) (not (at ?ag ?from)))
  )

  (:action assemble
    :parameters (?ag - agent ?p1 - part ?h1 - holder ?p2 - part ?h2 - holder ?p12 - part)
    :precondition (and (on ?p1 ?h1) (belong ?ag ?h1) (on ?p2 ?h2) (belong ?ag ?h2) (getnew ?p1 ?p2 ?p12))
    :effect (and (not (on ?p1 ?h1)) (not (on ?p2 ?h2)) (on ?p12 ?h2) (free ?h1))
  )
)