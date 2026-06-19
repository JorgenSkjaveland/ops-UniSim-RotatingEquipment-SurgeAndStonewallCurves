### Calculation method

#### Surge Line 

The surge line was calculated by finding two points. The first point is the surge point on the lowest speed curve. The second point is the surge point on the highest speed curve. The point is defined as a margin from the end of the curve. This curve is given as a percentage of the whole span of flow rates for that particualr speed. The surge point is calculated as follows:

$$
\text{Surge Point} = F_{min} + (F_{max} - F_{min}) \cdot margin\%
$$


Where $F_{min}$ is the minimum flow rate for that speed, $F_{max}$ is the maximum flow rate for that speed and $margin$ is the percentage margin from the end of the curve.

The two boundary points are then used to fit a linear curve, which is the surge line. The surge line is then plotted together with the low speed and high speed curves.

##### Plot of the Surge Line

Here is an example of the surge line with 10\% margin and one with 20\% margin. The surge line is plotted together with the low speed and high speed curves.

![Surge Line Plot](Images/10prctSurgeLine.png)

![Surge Line Plot](Images/20prctSurgeLine.png)

