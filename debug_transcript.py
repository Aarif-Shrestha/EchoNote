"""
Debug script to see raw MeetingBaas transcript data
"""
from meetingbaas_integration import get_transcript
import json

bot_id = "058427fe-c53c-4c7e-b517-4f333c879a3f"

print(f"Fetching transcript for bot: {bot_id}\n")

result = get_transcript(bot_id)

print("=" * 60)
print("RESULT:")
print(json.dumps(result, indent=2, default=str))
print("=" * 60)

if result.get('raw_data'):
    print("\nRAW TRANSCRIPT SEGMENTS:")
    transcripts = result['raw_data'].get('bot_data', {}).get('transcripts', [])
    for i, segment in enumerate(transcripts[:5]):  # Show first 5 segments
        print(f"\nSegment {i+1}:")
        print(f"  Speaker: {segment.get('speaker')}")
        print(f"  Words count: {len(segment.get('words', []))}")
        if segment.get('words'):
            print(f"  First 3 words: {segment['words'][:3]}")
        print(f"  Raw segment keys: {list(segment.keys())}")
