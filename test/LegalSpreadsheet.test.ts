import { isKeyword } from "../LegalSpreadsheet"

test('two plus two is four', () => {
    expect(isKeyword('IF')).toBe(true);
});
