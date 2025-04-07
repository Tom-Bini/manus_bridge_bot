# Recherche sur les Services de Bridge Crypto

## 1. Jumper (basé sur LI.FI)

Jumper est un agrégateur de bridges crypto basé sur l'API LI.FI. Il permet de réaliser des transferts d'actifs entre différentes blockchains.

### Caractéristiques principales
- Agrégateur multi-chaîne permettant des swaps et bridges entre 25 blockchains
- Basé sur l'API LI.FI
- Optimise les routes pour les transferts cross-chain

### API LI.FI
L'API LI.FI est une API REST qui permet de trouver les routes optimales pour effectuer des swaps et des bridges entre différentes blockchains.

#### Endpoints principaux
- `/quote` : Obtenir un devis pour un transfert de tokens
- Deux méthodes de demande de devis :
  - Par montant d'envoi (`fromAmount`)
  - Par montant de réception (`toAmount`)

#### Exemple d'utilisation de l'API
```javascript
const getQuote = async (fromChain, toChain, fromToken, toToken, fromAmount, fromAddress) => {
    const result = await axios.get('https://li.quest/v1/quote', {
        params: {
            fromChain,
            toChain,
            fromToken,
            toToken,
            fromAmount,
            fromAddress,
        }
    });
    return result.data;
}

const fromChain = 'DAI';
const fromToken = 'USDC';
const toChain = 'POL';
const toToken = 'USDC';
const fromAmount = '1000000';
const fromAddress = YOUR_WALLET_ADDRESS;

const quote = await getQuote(fromChain, toChain, fromToken, toToken, fromAmount, fromAddress);
```

## 2. Stargate

Stargate est un protocole de bridge natif entièrement composable construit sur LayerZero.

### Caractéristiques principales
- Premier bridge entièrement composable d'actifs natifs
- Construit sur LayerZero
- Offre une finalité garantie instantanée
- Utilise des actifs natifs plutôt que des actifs enveloppés
- Dispose de pools de liquidité unifiés

### Fonctionnalités
- Les utilisateurs DeFi peuvent échanger des actifs natifs cross-chain en une seule transaction
- Les applications peuvent composer Stargate pour créer des transactions cross-chain natives au niveau de l'application
- Les swaps cross-chain sont soutenus par les pools de liquidité unifiés de Stargate

### Avantages
1. **Finalité garantie instantanée** : Les utilisateurs peuvent faire confiance au fait que lorsqu'ils valident une transaction sur la chaîne source, elle arrivera sur la chaîne de destination.
2. **Actifs natifs** : Les utilisateurs échangent des actifs natifs plutôt que des actifs enveloppés qui nécessitent des swaps supplémentaires.
3. **Liquidité unifiée** : Accès partagé à un pool de liquidité unique sur plusieurs chaînes.

## 3. Relay

Relay est un service qui permet des bridges instantanés et des exécutions cross-chain.

### Caractéristiques principales
- API pour le bridging instantané
- API pour l'exécution cross-chain
- Permet de réaliser des swaps et des bridges entre différentes blockchains

### API Relay
L'API Relay offre plusieurs endpoints pour exploiter pleinement les outils de Relay.

#### Endpoints principaux
- `Get Chains` : Renvoie toutes les chaînes disponibles
- `Get Token Price` : Renvoie le prix d'un token sur une chaîne spécifique
- `Get Quote` : Obtenir un devis exécutable pour un bridge, un swap ou un appel
- `Get Execution Status` : Renvoie l'état d'exécution actuel
- `Get Request` : Renvoie toutes les transactions cross-chain
- `Transactions Index` : Notifie le backend d'une transaction
- `Multi-input Quote` : Obtenir un devis exécutable pour échanger des tokens de plusieurs chaînes d'origine vers une seule chaîne de destination

## Comparaison et Intégration

Pour notre bot, nous pouvons utiliser ces trois services de la manière suivante :

1. **Jumper/LI.FI** : Utiliser l'API LI.FI pour obtenir les meilleures routes pour les bridges et swaps cross-chain.
2. **Stargate** : Utiliser Stargate pour les bridges directs entre blockchains supportées, profitant de sa finalité garantie instantanée et de ses actifs natifs.
3. **Relay** : Utiliser Relay comme alternative pour certains bridges ou pour des fonctionnalités spécifiques comme les multi-input quotes.

### Stratégie d'intégration
- Implémenter une interface commune pour les trois services
- Sélectionner le service optimal en fonction des chaînes source et destination, des tokens et des frais
- Permettre une rotation entre les services pour diversifier les transactions

### Blockchains et Tokens supportés
Chaque service supporte différentes blockchains et tokens. Notre bot devra vérifier la compatibilité avant d'exécuter une transaction.

## Prochaines étapes
1. Explorer plus en détail les APIs de chaque service
2. Tester les appels API pour comprendre les formats de réponse
3. Développer une interface commune pour les trois services
4. Implémenter la logique de sélection du service optimal pour chaque transaction
