import 'package:flutter/material.dart';

void main() => runApp(const TurismoSCApp());

class TurismoSCApp extends StatelessWidget {
  const TurismoSCApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Turismo Santa Catarina',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(primarySwatch: Colors.green),
      home: const TurismoSCPage(),
    );
  }
}

class TurismoSCPage extends StatefulWidget {
  const TurismoSCPage({super.key});

  @override
  State<TurismoSCPage> createState() => _TurismoSCPageState();
}

class _TurismoSCPageState extends State<TurismoSCPage> {
  int rating = 0; 

  void updateRating(int value) {
    setState(() {
      rating = value;
    });
  }

  void showActionMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), duration: const Duration(seconds: 1)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Turismo Santa Catarina')),
      body: SingleChildScrollView(
        child: Column(
          children: [
            TurismoImage(
              imageUrl:
                  'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80',
              caption: 'Praia do Santinho, Florianópolis',
            ),

            const Padding(
              padding: EdgeInsets.all(24),
              child: Text(
                'Santa Catarina é um destino encantador, repleto de praias paradisíacas, '
                'montanhas impressionantes e cidades cheias de cultura. Aqui você encontra '
                'trilhas, esportes radicais e gastronomia típica. Venha conhecer este estado '
                'cheio de aventuras e paisagens inesquecíveis!',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 16, height: 1.5),
              ),
            ),

            const SizedBox(height: 10),

            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                GestureDetector(
                  onTap: () => showActionMessage('Ligando para o local...'),
                  child: const ButtonWithText(
                      icon: Icons.call, label: 'CALL', color: Colors.green),
                ),
                GestureDetector(
                  onTap: () => showActionMessage('Abrindo rota...'),
                  child: const ButtonWithText(
                      icon: Icons.map, label: 'ROUTE', color: Colors.green),
                ),
                GestureDetector(
                  onTap: () => showActionMessage('Compartilhando local...'),
                  child: const ButtonWithText(
                      icon: Icons.share, label: 'SHARE', color: Colors.green),
                ),
              ],
            ),

            const SizedBox(height: 20),

            Text(
              'Avalie este local:',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(5, (index) {
                return IconButton(
                  icon: Icon(
                    index < rating ? Icons.star : Icons.star_border,
                    color: Colors.orange,
                    size: 32,
                  ),
                  onPressed: () => updateRating(index + 1),
                );
              }),
            ),
            const SizedBox(height: 8),
            Text(
              '$rating / 5 estrelas',
              style: const TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }
}


class TurismoImage extends StatelessWidget {
  const TurismoImage({super.key, required this.imageUrl, required this.caption});

  final String imageUrl;
  final String caption;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Image.network(
          imageUrl,
          width: double.infinity,
          height: 240,
          fit: BoxFit.cover,
        ),
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Text(
            caption,
            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
          ),
        ),
      ],
    );
  }
}


class ButtonWithText extends StatelessWidget {
  const ButtonWithText({
    super.key,
    required this.color,
    required this.icon,
    required this.label,
  });

  final Color color;
  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(icon, color: color, size: 30),
        const SizedBox(height: 6),
        Text(
          label,
          style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: color),
        ),
      ],
    );
  }
}
