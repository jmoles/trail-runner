QPropertyAnimation *animation = new QPropertyAnimation(myWidget, "geometry");
animation->setDuration(10000);
animation->setStartValue(QRect(0, 0, 100, 30));
animation->setEndValue(QRect(250, 250, 100, 30));

animation->start();