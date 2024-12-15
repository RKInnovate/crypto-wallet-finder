"""
Cryptocurrency Wallet Address Generator.

This module provides functionality to generate wallet addresses for multiple
cryptocurrency chains from a single BIP39 seed phrase. It supports popular
blockchains including Ethereum, Bitcoin (SegWit), Binance Smart Chain,
TRON, and Solana.

The implementation follows BIP39, BIP44, and BIP84 standards for
deterministic wallet generation, ensuring compatibility with major
wallet providers.

Example:
    >>> from crypto_wallet import CryptoWallet
    >>> wallet = CryptoWallet("your twelve word seed phrase here")
    >>> addresses = wallet.get_addresses()
    >>> print(addresses['address']['eth'])  # Print Ethereum address
    >>> print(addresses['address']['btc'])  # Print Bitcoin address

Note:
    This module requires the bip_utils library for BIP39 seed generation
    and wallet derivation.

Attributes:
    None
"""


from bip_utils import (
    Bip39MnemonicValidator,
    Bip39SeedGenerator,
    Bip44,
    Bip84,
    Bip84Coins,
    Bip44Coins,
    Bip44Changes
)


class CryptoWallet:
    """A cryptocurrency wallet address generator supporting multiple chains.

    This class generates cryptocurrency wallet addresses for different
    blockchain networks using a single BIP39 seed phrase. It supports
    address generation for:
        - Ethereum (ETH)
        - Bitcoin (BTC) using SegWit/Bech32
        - Binance Smart Chain (BNB)
        - TRON (TRX)
        - Solana (SOL)

    The wallet addresses are derived following BIP44 and BIP84 standards,
    making them compatible with most cryptocurrency wallets and exchanges.

    Args:
        seed_phrase (str): A valid BIP39 seed phrase (usually 12 or 24 words)

    Raises:
        ValueError: If the provided seed phrase is invalid according to BIP39 standard

    Example:
        >>> wallet = CryptoWallet("word1 word2 ... word12")
        >>> eth_address = wallet.get_eth_address()
        >>> all_addresses = wallet.get_addresses()
    """

    def __init__(self, seed_phrase: str) -> None:
        """Initialize the wallet with a BIP39 seed phrase.

        Args:
            seed_phrase (str): A valid BIP39 seed phrase

        Raises:
            ValueError: If the seed phrase is invalid
        """
        self.seed_phrase = seed_phrase
        self.validate_seed_phrase()
        self.seed = Bip39SeedGenerator(seed_phrase).Generate()
        self.bip44_mst = Bip44.FromSeed(self.seed, Bip44Coins.ETHEREUM)

    def validate_seed_phrase(self) -> None:
        """Validate that the seed phrase follows BIP39 standard.

        Raises:
            ValueError: If the seed phrase is invalid according to BIP39
        """
        validator = Bip39MnemonicValidator()
        if not validator.IsValid(self.seed_phrase):
            raise ValueError(f"Invalid BIP39 seed phrase: {self.seed_phrase}")

    def get_eth_address(self) -> str:
        """Generate an Ethereum (ETH) address.

        The address is derived using BIP44 with coin type 60 (ETH).

        Returns:
            str: A valid Ethereum address starting with '0x'
        """
        return self.bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0).PublicKey().ToAddress()

    def get_btc_address(self) -> str:
        """Generate a Bitcoin (BTC) SegWit address.

        The address is derived using BIP84 (Native SegWit) with
        coin type 0 (BTC) and uses Bech32 encoding.

        Returns:
            str: A Bech32 Bitcoin address starting with 'bc1'
        """
        btc_wallet = Bip84.FromSeed(self.seed, Bip84Coins.BITCOIN)
        segwit_wallet = btc_wallet.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
        return segwit_wallet.PublicKey().ToAddress()

    def get_bnb_address(self) -> str:
        """Generate a Binance Smart Chain (BNB) address.

        Uses the same address format as Ethereum since BSC is
        EVM-compatible. The address can be used for BEP20 tokens.

        Returns:
            str: A BSC address (same format as Ethereum)
        """
        return self.get_eth_address()

    def get_trx_address(self) -> str:
        """Generate a TRON (TRX) address.

        The address is derived using BIP44 with TRON's coin type
        and uses Base58 encoding.

        Returns:
            str: A TRON address starting with 'T'
        """
        trx_wallet = Bip44.FromSeed(self.seed, Bip44Coins.TRON)
        return trx_wallet.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0).PublicKey().ToAddress()
    
    def get_sol_address(self) -> str:
        """Generate a Solana (SOL) address.

        The address is derived using BIP44 with Solana's coin type
        and uses Base58 encoding.

        Returns:
            str: A Solana address in Base58 format
        """
        sol_wallet = Bip44.FromSeed(self.seed, Bip44Coins.SOLANA)
        return sol_wallet.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0).PublicKey().ToAddress()

    def get_addresses(self) -> dict:
        """Generate addresses for all supported cryptocurrencies.

        Returns:
            dict: A dictionary containing:
                - 'seed': The original seed phrase
                - 'address': A dictionary mapping coin symbols to addresses
                    - 'eth': Ethereum address
                    - 'btc': Bitcoin address
                    - 'bnb': Binance Smart Chain address
                    - 'trx': TRON address
                    - 'sol': Solana address
        """
        return {
            'seed': self.seed_phrase,
            'address': {
                "eth": self.get_eth_address(),
                "btc": self.get_btc_address(),
                "bnb": self.get_bnb_address(),
                "trx": self.get_trx_address(),
                "sol": self.get_sol_address()
            }
        }
