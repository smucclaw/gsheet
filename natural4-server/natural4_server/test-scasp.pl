:-module('test-scasp', []).
:- set_prolog_flag(scasp_lang, en).
% s(CASP) Programming 
:- use_module(library(scasp)).
% Uncomment to suppress warnings
:- style_check(-discontiguous).
:- style_check(-singleton).
:- set_prolog_flag(scasp_forall, prev).
/** <examples>
**/