-- ====================================
--Datos iniciales para la API de Música

-- 5 usuarios
INSERT INTO usuario (nombre, correo, fecha_registro) VALUES
  ('Laura Martínez',   'laura.martinez@mail.com', CURRENT_TIMESTAMP),
  ('Andrés Rodríguez', 'andres.rodriguez@mail.com', CURRENT_TIMESTAMP),
  ('Valentina Gómez',  'valentina.gomez@mail.com', CURRENT_TIMESTAMP),
  ('Santiago López',   'santiago.lopez@mail.com', CURRENT_TIMESTAMP),
  ('Camila Torres',    'camila.torres@mail.com', CURRENT_TIMESTAMP);

-- 10 canciones (duracion en segundos)
INSERT INTO cancion (titulo, artista, album, duracion, "año", genero, fecha_creacion) VALUES
  ('La Bicicleta',          'Carlos Vives y Shakira', 'Vives',                 227, 2016, 'Vallenato pop', CURRENT_TIMESTAMP),
  ('Bohemian Rhapsody',     'Queen',                  'A Night at the Opera',  354, 1975, 'Rock',          CURRENT_TIMESTAMP),
  ('Hips Don''t Lie',       'Shakira',                'Oral Fixation Vol. 2',  218, 2006, 'Pop latino',    CURRENT_TIMESTAMP),
  ('Despacito',             'Luis Fonsi',             'Vida',                  229, 2017, 'Reguetón',      CURRENT_TIMESTAMP),
  ('Billie Jean',           'Michael Jackson',        'Thriller',              294, 1982, 'Pop',           CURRENT_TIMESTAMP),
  ('De Música Ligera',      'Soda Stereo',            'Canción Animal',        211, 1990, 'Rock en español', CURRENT_TIMESTAMP),
  ('Tusa',                  'Karol G',                'KG0516',                200, 2019, 'Reguetón',      CURRENT_TIMESTAMP),
  ('Smells Like Teen Spirit','Nirvana',               'Nevermind',             301, 1991, 'Grunge',        CURRENT_TIMESTAMP),
  ('La Gota Fría',          'Carlos Vives',           'Clásicos de la Provincia', 270, 1993, 'Vallenato',  CURRENT_TIMESTAMP),
  ('Blinding Lights',       'The Weeknd',             'After Hours',           200, 2019, 'Synth-pop',     CURRENT_TIMESTAMP);

-- Verificación
SELECT COUNT(*) AS total_usuarios FROM usuario;
SELECT COUNT(*) AS total_canciones FROM cancion;
