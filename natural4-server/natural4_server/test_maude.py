from pathlib import Path

from natural4_maude.analyse_state_space import run_analyse_state_space


def main():
    natural4_file = Path('natural4_maude') / 'examples' / 'loan-agreement.natural4'
    output_path = Path('.temp')
    run_analyse_state_space(natural4_file, output_path)


if __name__ == '__main__':
    main()
