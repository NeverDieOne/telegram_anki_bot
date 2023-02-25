import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

from anki.collection import Collection
from anki.decks import Deck, DeckId, DeckDict
from anki.cards import Card
from anki.notes import Note
from anki.models import NotetypeId

from settings import settings


logger = logging.getLogger('anki_api')


class AnkiCollection:
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        self.user_coll_dir = Path(settings.BASE_USERS_PATH) / str(self.user_id)
        self.user_coll_dir.mkdir(parents=True, exist_ok=True)
        self.user_coll_path = self.user_coll_dir / 'coll.anki2'

    def get_collection(self) -> Collection:
        """Get user collection. Don't forget to close it.

        Returns:
            Collection: Collection object for user.
        """
        return Collection(self.user_coll_path.as_posix())

    @contextmanager
    def collection(self) -> Generator[Collection, None, None]:
        coll = Collection(self.user_coll_path.as_posix())
        try:
            yield coll
        finally:
            coll.close()

    def create_deck(self, deck_name: str) -> int:
        """Adding a new deck to the user's collection.

        Args:
            deck_name (str): Name for a new deck.

        Returns:
            int: New deck id.
        """
        with self.collection() as coll:
            deck = coll.decks.new_deck()
            deck.name = deck_name
            res = coll.decks.add_deck(deck)
            return res.id
        
    def get_default_model(self, ) -> dict[str, Any]:
        """Get default model as dict.

        Returns:
            dict[str, Any]: Dict view of model with name Basic.
        """
        with self.collection() as coll:
            models = coll.models.all_names_and_ids()
            model_id = None
            for model in models:
                if model.name == 'Basic':
                    model_id = model.id
                    break
            assert model_id, 'Can not find basic model'
                
            basic_model = coll.models.get(NotetypeId(model_id))
            return basic_model
        
    def add_card(
        self,
        deck_id: int,
        model: dict[str, Any],
        front: str,
        back: str
    ) -> int:
        """Add card in deck.

        Args:
            deck_id (int): Deck id to add card.
            model (dict[str, Any]): Model description for card.
            front (str): Front of the card.
            back (str): Back of the card.

        Returns:
            int: New card id.
        """
        with self.collection() as coll:
            new_note = coll.new_note(model)
            new_note.fields = [front, back]
            coll.add_note(new_note, DeckId(deck_id))
            coll.after_note_updates([new_note.id], True, True)
            return new_note.cards()[0].id
        
    
    def get_decks(
        self,
        skip_default: bool = True
    ) -> list[tuple[str, int]]:
        """Get decks names with ids.

        Args:
            skip_default (bool, optional): Skip default deck if it's empty. Defaults to True.

        Returns:
            list[tuple[str, int]]: List of deck name and deck id.
        """
        with self.collection() as coll:
            return [
                (d.name, d.id) for d in coll.decks.all_names_and_ids(skip_default)
            ]
        
    def get_current_deck(self) -> DeckDict:
        """Get current deck as dick.

        Returns:
            DeckDict: Dict representation of deck.
        """
        with self.collection() as coll:
            return coll.decks.current()
        
    
    def set_deck(self, deck_id: int) -> None:
        """Set deck by ID.

        Args:
            deck_id (int): Deck ID to change to.
        """
        with self.collection() as coll:
            coll.decks.select(DeckId(deck_id))

    def get_queues_count(self) -> tuple[int, int, int]:
        """Get queued cards count.

        Returns:
            tuple[int, int, int]: New count, rev count, learn count cards.
        """
        with self.collection() as coll:
            res = coll._backend.get_queued_cards(
                fetch_limit=None, intraday_learning_only=False
            )
            return (res.new_count, res.review_count, res.learning_count)
        
    def find_cards(self, query: str = '') -> list[int] | None:
        """Find cards by query or all.

        Args:
            query (str, optional): Query . Defaults to ''.

        Returns:
            list[int] | None: _description_
        """
        with self.collection() as coll:
            return [c for c in coll.find_cards(query)]
        
    def get_card_and_note(self) -> tuple[Card, Note]:
        """Get next card with note to learning.

        Returns:
            tuple[Card, Note]: Card and note for this card.
        """
        with self.collection() as coll:
            card = coll.sched.getCard()
            return card, card.note()
        
    def get_next_time_buttons(self, card: Card) -> list[str]:
        """Button descriptions for all ease for card.

        Args:
            card (Card): Card to get times.

        Returns:
            list[str]: Day count for ease from 1 to 4.
        """
        with self.collection() as coll:
            res: list[str] = []
            for ease in range(1, 5):
                res.append(coll.sched.nextIvlStr(card, ease).strip())
            return res
        
    def sync_collection(self, username: str, password: str) -> None:
        """Synchronize collections between bot and anki server.

        Args:
            username (str): Username from anki server.
            password (str): Password from anki server.
        """
        with self.collection() as coll:
            auth = coll.sync_login(
                username=username, password=password, endpoint=None
            )
            coll.close_for_full_sync()
            res = coll.sync_collection(auth)
            auth.endpoint = res.new_endpoint
            coll.full_download(auth)
            coll.full_upload(auth)
