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
                , andOr = Simply "walks"
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
                        , andOr = Simply "drinks"
                        , prePost = Nothing
                        , mark = Default ( Left Nothing )
                        }
                    , subForest = []
                    }
                , Node
                    { rootLabel = Q
                        { shouldView = Ask
                        , andOr = Simply "eats"
                        , prePost = Nothing
                        , mark = Default ( Left Nothing )
                        }
                    , subForest = []
                    }
                ]
            }
        ]
    }