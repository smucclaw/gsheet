Node
    { rootLabel = Q
        { shouldView = View
        , andOr = And
        , prePost = Nothing
        , mark = Default ( Left Nothing )
        }
    , subForest =
        [ Node
            { rootLabel = Q
                { shouldView = Ask
                , andOr = Simply "Person walks"
                , prePost = Nothing
                , mark = Default ( Left Nothing )
                }
            , subForest = []
            }
        , Node
            { rootLabel = Q
                { shouldView = View
                , andOr = Or
                , prePost = Nothing
                , mark = Default ( Left Nothing )
                }
            , subForest =
                [ Node
                    { rootLabel = Q
                        { shouldView = Ask
                        , andOr = Simply "Person eats"
                        , prePost = Nothing
                        , mark = Default ( Left Nothing )
                        }
                    , subForest = []
                    }
                , Node
                    { rootLabel = Q
                        { shouldView = Ask
                        , andOr = Simply "Person drinks"
                        , prePost = Nothing
                        , mark = Default ( Left Nothing )
                        }
                    , subForest = []
                    }
                ]
            }
        ]
    }