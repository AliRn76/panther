from pydantic import BaseModel, Field

from panther import Panther, status
from panther.app import GenericAPI
from panther.request import Request
from panther.response import Response


class CreateNoteInput(BaseModel):
    text: str = Field(min_length=1)


NOTES: dict[int, str] = {
    1: 'Class-based endpoints are useful when one URL supports many methods.',
}


class NotesAPI(GenericAPI):
    input_model = CreateNoteInput

    async def get(self):
        return [{'id': note_id, 'text': text} for note_id, text in NOTES.items()]

    async def post(self, request: Request):
        note_id = max(NOTES, default=0) + 1
        NOTES[note_id] = request.validated_data.text
        return Response(data={'id': note_id, 'text': NOTES[note_id]}, status_code=status.HTTP_201_CREATED)


class NoteDetailAPI(GenericAPI):
    async def get(self, note_id: int):
        if note_id not in NOTES:
            return Response(data={'detail': 'Note not found'}, status_code=status.HTTP_404_NOT_FOUND)
        return {'id': note_id, 'text': NOTES[note_id]}

    async def delete(self, note_id: int):
        if note_id not in NOTES:
            return Response(data={'detail': 'Note not found'}, status_code=status.HTTP_404_NOT_FOUND)
        deleted = NOTES.pop(note_id)
        return {'id': note_id, 'deleted': deleted}


url_routing = {
    'notes/': NotesAPI,
    'notes/<note_id>/': NoteDetailAPI,
}

app = Panther(__name__, configs=__name__, urls=url_routing)
