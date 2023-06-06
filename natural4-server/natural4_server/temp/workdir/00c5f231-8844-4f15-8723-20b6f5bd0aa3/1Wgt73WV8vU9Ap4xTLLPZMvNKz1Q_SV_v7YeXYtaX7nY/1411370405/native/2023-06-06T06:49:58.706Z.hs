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
        ( Leaf
            ( RPMT
                [ MTT "Qualifies" ]
            )
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
            { url = "./temp/workdir/00c5f231-8844-4f15-8723-20b6f5bd0aa3/1Wgt73WV8vU9Ap4xTLLPZMvNKz1Q_SV_v7YeXYtaX7nY/1411370405/20230606T064958.639896Z.csv"
            , short = "./temp/workdir/00c5f231-8844-4f15-8723-20b6f5bd0aa3/1Wgt73WV8vU9Ap4xTLLPZMvNKz1Q_SV_v7YeXYtaX7nY/1411370405/20230606T064958.639896Z.csv"
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
, Hornlike
    { name =
        [ MTT "Qualifies" ]
    , super = Nothing
    , keyword = Means
    , given = Nothing
    , giveth = Nothing
    , upon = Nothing
    , clauses =
        [ HC
            { hHead = RPBoolStructR
                [ MTT "Qualifies" ] RPis
                ( All Nothing
                    [ Leaf
                        ( RPMT
                            [ MTT "walks" ]
                        )
                    , Any Nothing
                        [ Leaf
                            ( RPMT
                                [ MTT "drinks" ]
                            )
                        , Leaf
                            ( RPMT
                                [ MTT "eats" ]
                            )
                        ]
                    ]
                )
            , hBody = Nothing
            }
        ]
    , rlabel = Nothing
    , lsource = Nothing
    , srcref = Just
        ( SrcRef
            { url = "./temp/workdir/00c5f231-8844-4f15-8723-20b6f5bd0aa3/1Wgt73WV8vU9Ap4xTLLPZMvNKz1Q_SV_v7YeXYtaX7nY/1411370405/20230606T064958.639896Z.csv"
            , short = "./temp/workdir/00c5f231-8844-4f15-8723-20b6f5bd0aa3/1Wgt73WV8vU9Ap4xTLLPZMvNKz1Q_SV_v7YeXYtaX7nY/1411370405/20230606T064958.639896Z.csv"
            , srcrow = 6
            , srccol = 8
            , version = Nothing
            }
        )
    , defaults = []
    , symtab = []
    }
]
-- variable-substitution expanded AnyAll rules

[ Hornlike
    { name =
        [ MTT "Qualifies" ]
    , super = Nothing
    , keyword = Means
    , given = Nothing
    , giveth = Nothing
    , upon = Nothing
    , clauses =
        [ HC
            { hHead = RPBoolStructR
                [ MTT "Qualifies" ] RPis
                ( All Nothing
                    [ Leaf
                        ( RPMT
                            [ MTT "walks" ]
                        )
                    , Any Nothing
                        [ Leaf
                            ( RPMT
                                [ MTT "drinks" ]
                            )
                        , Leaf
                            ( RPMT
                                [ MTT "eats" ]
                            )
                        ]
                    ]
                )
            , hBody = Nothing
            }
        ]
    , rlabel = Nothing
    , lsource = Nothing
    , srcref = Just
        ( SrcRef
            { url = "./temp/workdir/00c5f231-8844-4f15-8723-20b6f5bd0aa3/1Wgt73WV8vU9Ap4xTLLPZMvNKz1Q_SV_v7YeXYtaX7nY/1411370405/20230606T064958.639896Z.csv"
            , short = "./temp/workdir/00c5f231-8844-4f15-8723-20b6f5bd0aa3/1Wgt73WV8vU9Ap4xTLLPZMvNKz1Q_SV_v7YeXYtaX7nY/1411370405/20230606T064958.639896Z.csv"
            , srcrow = 6
            , srccol = 8
            , version = Nothing
            }
        )
    , defaults = []
    , symtab = []
    }
]


-- class hierarchy:

CT
    ( fromList [] )


-- symbol table:

fromList
    [
        (
            [ MTT "Qualifies" ]
        , fromList
            [
                (
                    [ MTT "Qualifies" ]
                ,
                    (
                        ( Nothing
                        , []
                        )
                    ,
                        [ HC
                            { hHead = RPBoolStructR
                                [ MTT "Qualifies" ] RPis
                                ( All Nothing
                                    [ Leaf
                                        ( RPMT
                                            [ MTT "walks" ]
                                        )
                                    , Any Nothing
                                        [ Leaf
                                            ( RPMT
                                                [ MTT "drinks" ]
                                            )
                                        , Leaf
                                            ( RPMT
                                                [ MTT "eats" ]
                                            )
                                        ]
                                    ]
                                )
                            , hBody = Nothing
                            }
                        ]
                    )
                )
            ]
        )
    ]
-- getAndOrTrees

-- [MTT "Person"]
Just
    ( Leaf "Person Qualifies" )

-- [MTT "Qualifies"]
Just
    ( All Nothing
        [ Leaf "walks"
        , Any Nothing
            [ Leaf "drinks"
            , Leaf "eats"
            ]
        ]
    )

-- traverse toList of the getAndOrTrees
[ Just "Person Qualifies" ]
[ Just "walks"
, Just "drinks"
, Just "eats"
]

-- onlyTheItems
All Nothing
    [ Leaf "Person Qualifies"
    , Leaf "walks"
    , Any Nothing
        [ Leaf "drinks"
        , Leaf "eats"
        ]
    ]
-- ItemsByRule
[
    (
        [ MTT "Person" ]
    , Leaf "Person Qualifies"
    )
,
    (
        [ MTT "Qualifies" ]
    , All Nothing
        [ Leaf "walks"
        , Any Nothing
            [ Leaf "drinks"
            , Leaf "eats"
            ]
        ]
    )
]
