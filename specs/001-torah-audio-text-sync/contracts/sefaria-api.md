# Sefaria API Contract  
  
**Date**: 2026-01-31  
**Purpose**: Define expected behavior and interface for Sefaria REST API v3 integration  
  
## Base URL  
  
```  
https://www.sefaria.org/api  
```  
  
## Endpoint: Get Text  
  
**URL**: `/texts/{ref}`  
  
**Method**: GET  
  
**Description**: Retrieve Hebrew text for a specific biblical reference  
  
### Request Parameters  
  
**Path Parameter**:  
- `ref` (string, required): Biblical reference in format `{Book}.{Chapter}.{Verse}`  
  - Examples: `Genesis.1.1`, `Deuteronomy.32.1`  
  - Book names must use English transliteration  
  
**Query Parameters**:  
- `context` (int, optional): Number of surrounding verses to include  
- `commentary` (int, optional): Whether to include commentary (0=no, 1=yes, default=0)  
- `pad` (int, optional): Pad to complete section (0=no, 1=yes, default=0)  
  
### Response Format  
  
**Success (200 OK)**:  
```json  
{  
  "ref": "Deuteronomy 32:1",  
  "heRef": "דברים ל״ב:א׳",  
  "text": ["הַאֲזִ֥ינוּ הַשָּׁמַ֖יִם וַאֲדַבֵּ֑רָה וְתִשְׁמַ֥ע הָאָ֖רֶץ אִמְרֵי־פִֽי׃"],  
  "he": ["הַאֲזִ֥ינוּ הַשָּׁמַ֖יִם וַאֲדַבֵּ֑רָה וְתִשְׁמַ֥ע הָאָ֖רֶץ אִמְרֵי־פִֽי׃"],  
  "versionTitle": "Miqra according to the Masorah",  
  "lang": "he",  
  "sectionRef": "Deuteronomy 32:1",  
  "sections": ["Deuteronomy", "32", "1"]  
}  
```  
  
**Error (404 Not Found)**:  
```json  
{  
  "error": "Could not find ref: InvalidBook.1.1"  
}  
```  
  
**Error (500 Internal Server Error)**:  
```json  
{  
  "error": "Internal server error"  
}  
```  
  
### Field Descriptions  
  
- `ref`: English reference string  
- `heRef`: Hebrew reference string  
- `text`: Array of text strings (one per verse), English if requested  
- `he`: Array of Hebrew text strings with vowels (Nikkud) and cantillation marks (T'amim)  
- `versionTitle`: Source version name  
- `lang`: Language code ("he" for Hebrew)  
- `sectionRef`: Full section reference  
- `sections`: Array of section components  
  
### Required Fields for Our Use  
  
**MUST have**:  
- `he` field containing Hebrew text with Unicode diacritical marks  
- Hebrew text MUST include vowels (Unicode U+05B0–U+05BD range)  
- Hebrew text MUST include cantillation marks (Unicode U+0591–U+05AF range)  
  
**Validation**:  
```python  
def validate_sefaria_response(response: dict) -> bool:  
    """Validate Sefaria API response has required Hebrew text with diacritics"""  
    if "he" not in response or not response["he"]:  
        return False  
  
    hebrew_text = response["he"][0] if isinstance(response["he"], list) else response["he"]  
  
    # Check for vowel points (Nikkud)  
    has_nikkud = any('\u05B0' <= char <= '\u05BD' for char in hebrew_text)  
  
    # Check for cantillation marks (T'amim)  
    has_teamim = any('\u0591' <= char <= '\u05AF' for char in hebrew_text)  
  
    return has_nikkud and has_teamim  
```  
  
## Endpoint: Get Range  
  
**URL**: `/texts/{ref1}-{ref2}`  
  
**Method**: GET  
  
**Description**: Retrieve a range of verses  
  
### Example Request  
  
```http  
GET /api/texts/Deuteronomy.32.1-Deuteronomy.32.5  
```  
  
### Example Response  
  
```json  
{  
  "ref": "Deuteronomy 32:1-5",  
  "heRef": "דברים ל״ב:א׳-ה׳",  
  "text": [...],  
  "he": [  
    "הַאֲזִ֥ינוּ הַשָּׁמַ֖יִם וַאֲדַבֵּ֑רָה וְתִשְׁמַ֥ע הָאָ֖רֶץ אִמְרֵי־פִֽי׃",  
    "יַעֲרֹ֤ף כַּמָּטָר֙ לִקְחִ֔י תִּזַּ֥ל כַּטַּ֖ל אִמְרָתִ֑י כִּשְׂעִירִ֣ם עֲלֵי־דֶ֔שֶׁא וְכִרְבִיבִ֖ים עֲלֵי־עֵֽשֶׂב׃",  
    "כִּ֛י שֵׁ֥ם יְהֹוָ֖ה אֶקְרָ֑א הָב֥וּ גֹ֖דֶל לֵאלֹהֵֽינוּ׃",  
    "הַצּוּר֙ תָּמִ֣ים פׇּעֳל֔וֹ כִּ֥י כׇל־דְּרָכָ֖יו מִשְׁפָּ֑ט אֵ֤ל אֱמוּנָה֙ וְאֵ֣ין עָ֔וֶל צַדִּ֥יק וְיָשָׁ֖ר הֽוּא׃",  
    "שִׁחֵ֥ת ל֛וֹ לֹ֖א בָּנָ֣יו מוּמָ֑ם דּ֥וֹר עִקֵּ֖שׁ וּפְתַלְתֹּֽל׃"  
  ],  
  "versionTitle": "Miqra according to the Masorah"  
}  
```  
  
## Error Handling Strategy  
  
Per spec clarification: **Fail processing with clear error message when API unavailable**  
  
### Error Scenarios  
  
1. **Network Timeout**:  
   - Retry with exponential backoff (3 attempts)  
   - If all retries fail: Raise exception with message "Hebrew text source unavailable: Connection timeout"  
  
2. **Rate Limiting (429 Too Many Requests)**:  
   - Wait according to Retry-After header  
   - Retry request  
   - If persistent: Fail with message "Hebrew text source unavailable: Rate limit exceeded"  
  
3. **Invalid Reference (404)**:  
   - Do NOT retry  
   - Fail immediately with message "Invalid biblical reference: {ref}"  
  
4. **API Error (500, 502, 503)**:  
   - Retry with exponential backoff (3 attempts)  
   - If all retries fail: Raise exception with message "Hebrew text source unavailable: Server error"  
  
5. **Invalid Response (missing required fields)**:  
   - Do NOT retry  
   - Fail with message "Hebrew text incomplete: Missing vowels or cantillation marks"  
  
### Retry Configuration  
  
```python  
MAX_RETRIES = 3  
RETRY_BACKOFF_BASE = 2  # seconds  
RETRY_BACKOFF_MULTIPLIER = 2  
  
# Retry delays: 2s, 4s, 8s  
```  
  
### Caching Strategy  
  
**Cache Location**: `data/cache/sefaria/{book}_{chapter}_{verse}.json`  
  
**Cache Invalidation**: Never (biblical text doesn't change)  
  
**Cache Hit Behavior**: Return cached response without API call  
  
**Cache Miss Behavior**: Call API, validate response, save to cache, return result  
  
## Client Interface  
  
```python  
from typing import Protocol  
  
class HebrewTextSource(Protocol):  
    """Protocol for Hebrew text retrieval"""  
  
    def get_verse(self, book: str, chapter: int, verse: int) -> str:  
        """Get single verse text  
  
        Args:  
            book: Book name (e.g., "Deuteronomy")  
            chapter: Chapter number (1-indexed)  
            verse: Verse number (1-indexed)  
  
        Returns:  
            Hebrew text with vowels and cantillation marks  
  
        Raises:  
            HebrewTextUnavailableError: When API fails per FR-002a  
            InvalidReferenceError: When reference is invalid  
        """  
        ...  
  
    def get_range(  
        self,  
        book: str,  
        chapter_start: int,  
        verse_start: int,  
        chapter_end: int,  
        verse_end: int  
    ) -> list[tuple[str, str]]:  
        """Get range of verses  
  
        Args:  
            book: Book name  
            chapter_start: Starting chapter  
            verse_start: Starting verse  
            chapter_end: Ending chapter  
            verse_end: Ending verse  
  
        Returns:  
            List of (reference, hebrew_text) tuples  
  
        Raises:  
            HebrewTextUnavailableError: When API fails  
            InvalidReferenceError: When reference is invalid  
        """  
        ...  
```  
  
## Testing Contract  
  
**Contract Tests** must verify:  
  
1. **Successful retrieval**: API returns Hebrew text with diacritics  
2. **Invalid reference handling**: 404 errors handled correctly  
3. **Network failure handling**: Retries and eventual failure  
4. **Rate limiting handling**: Respects Retry-After header  
5. **Caching behavior**: Cache hits avoid API calls  
6. **Response validation**: Missing diacritics detected and rejected  
7. **Error messages**: Match expected format from FR-002a  
  
**Example Test**:  
```python  
def test_sefaria_api_unavailable():  
    """Client should raise HebrewTextUnavailableError when API fails"""  
    with patch('httpx.Client.get', side_effect=httpx.ConnectError):  
        client = SefariaClient()  
        with pytest.raises(HebrewTextUnavailableError) as exc_info:  
            client.get_verse("Deuteronomy", 32, 1)  
  
        assert "Hebrew text source unavailable" in str(exc_info.value)  
```  
  
## Rate Limiting  
  
Sefaria API has undocumented rate limits. Best practices:  
  
- **Implement delays**: 100ms between requests  
- **Respect 429 responses**: Wait for Retry-After duration  
- **Cache aggressively**: Avoid redundant requests  
- **Batch wisely**: Don't slam API with 300+ requests in quick succession  
  
## Legal & Attribution  
  
- **License**: Sefaria texts are CC0 (public domain) or CC-BY  
- **Attribution**: Include "Text from Sefaria.org" in video metadata (satisfies FR-010, FR-011)  
- **Commercial Use**: Allowed per Sefaria license  
