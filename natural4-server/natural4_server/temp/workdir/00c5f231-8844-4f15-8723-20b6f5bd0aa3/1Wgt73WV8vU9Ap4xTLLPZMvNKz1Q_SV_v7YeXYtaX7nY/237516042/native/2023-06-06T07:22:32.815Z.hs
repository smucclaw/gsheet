-- original rules:

[ Regulative
    { subj = Leaf
        (
            ( MTT "Person" :| []
            , Nothing
            ) :| []
        )
    , rkeyword = REvery
    , who = Just
        ( All Nothing
            [ Leaf
                ( RPMT
                    [ MTT "walks" ]
                )
            , Any Nothing
                [ Leaf
                    ( RPMT
                        [ MTT "eats" ]
                    )
                , Leaf
                    ( RPMT
                        [ MTT "drinks" ]
                    )
                ]
            ]
        )
    , cond = Nothing
    , deontic = DMust
    , action = Leaf
        (
            ( MTT "sing" :| []
            , Nothing
            ) :| []
        )
    , temporal = Nothing
    , hence = Nothing
    , lest = Nothing
    , rlabel = Nothing
    , lsource = Nothing
    , srcref = Just
        ( SrcRef
            { url = "./temp/workdir/00c5f231-8844-4f15-8723-20b6f5bd0aa3/1Wgt73WV8vU9Ap4xTLLPZMvNKz1Q_SV_v7YeXYtaX7nY/237516042/20230606T072232.783673Z.csv"
            , short = "./temp/workdir/00c5f231-8844-4f15-8723-20b6f5bd0aa3/1Wgt73WV8vU9Ap4xTLLPZMvNKz1Q_SV_v7YeXYtaX7nY/237516042/20230606T072232.783673Z.csv"
            , srcrow = 2
            , srccol = 1
            , version = Nothing
            }
        )
    , upon = Nothing
    , given = Nothing
    , having = Nothing
    , wwhere = []
    , defaults = []
    , symtab = []
    }
]
-- variable-substitution expanded AnyAll rules

[]


-- class hierarchy:

CT
    ( fromList [] )


-- symbol table:

fromList []
-- getAndOrTrees

-- [MTT "Person"]
Just
    ( All Nothing
        [ Leaf "Person walks"
        , Any Nothing
            [ Leaf "Person eats"
            , Leaf "Person drinks"
            ]
        ]
    )

-- traverse toList of the getAndOrTrees
[ Just "Person walks"
, Just "Person eats"
, Just "Person drinks"
]

-- onlyTheItems
All Nothing
    [ Leaf "Person walks"
    , Any Nothing
        [ Leaf "Person eats"
        , Leaf "Person drinks"
        ]
    ]
-- ItemsByRule
[
    (
        [ MTT "Person" ]
    , All Nothing
        [ Leaf "Person walks"
        , Any Nothing
            [ Leaf "Person eats"
            , Leaf "Person drinks"
            ]
        ]
    )
]
